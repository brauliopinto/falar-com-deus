import logging
import re
from dataclasses import asdict
from datetime import datetime
from urllib.parse import urlparse
from zoneinfo import ZoneInfo

from app.services.text_normalizer import normalize_text as _norm

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.meditacao import Meditacao
from app.schemas.meditacao import MeditacaoCreate
from app.services.scraper import ScrapedMeditation, ScraperService
from app.services.translator import TranslatorService

logger = logging.getLogger(__name__)


def _is_pt_url(url: str) -> bool:
    return bool(re.search(r"(^|/)pt(/|$)", urlparse(url).path))


def _translate_or_empty(translator: TranslatorService, text: str) -> str:
    if not text.strip():
        return ""
    result = translator.translate_es_to_pt(text)
    if text.strip().startswith("—") and not result.strip().startswith("—"):
        result = "— " + result.lstrip()
    return result


class MeditationService:
    def __init__(
        self,
        db: Session,
        scraper: ScraperService,
        translator: TranslatorService,
        pt_source_url: str,
    ) -> None:
        self._db = db
        self._scraper = scraper
        self._translator = translator
        self._pt_source_url = pt_source_url

    def get_today(self) -> Meditacao:
        today = datetime.now(ZoneInfo("America/Sao_Paulo")).strftime("%d/%m/%Y")
        meditation = self._db.scalar(select(Meditacao).where(Meditacao.data == today))
        if meditation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meditação de hoje ainda não foi carregada.",
            )
        return meditation

    def get_by_date(self, data: str) -> Meditacao:
        meditation = self._db.scalar(select(Meditacao).where(Meditacao.data == data))
        if meditation is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Meditação não encontrada para a data {data}.",
            )
        return meditation

    def list_all(self, limit: int, offset: int) -> tuple[list[Meditacao], int]:
        items = list(
            self._db.scalars(
                select(Meditacao).order_by(func.to_date(Meditacao.data, "DD/MM/YYYY").desc()).offset(offset).limit(limit),
            ),
        )
        total = self._db.query(Meditacao).count()
        return items, total

    def scrape_and_store_today(
        self,
        force_refresh: bool = False,
        source_url: str | None = None,
        target_date: datetime | None = None,
        translate: bool | None = None,
    ) -> tuple[Meditacao, bool]:
        effective_date = target_date or datetime.now(ZoneInfo("America/Sao_Paulo"))

        if source_url is not None:
            scraped = self._scraper.scrape_for_date(source_url=source_url, target_date=effective_date)
            should_translate = translate if translate is not None else not _is_pt_url(source_url)
            if should_translate:
                return self._persist_scraped(original=scraped, pt_scraped=None, force_refresh=force_refresh)
            return self._persist_scraped(original=scraped, pt_scraped=scraped, force_refresh=force_refresh)

        try:
            pt_scraped = self._scraper.scrape_for_date(source_url=self._pt_source_url, target_date=effective_date)
        except Exception:
            logger.warning(
                "Falha ao obter a meditação diretamente em português (%s). "
                "Usando raspagem da página em espanhol com tradução via LLM/DeepL como fallback.",
                self._pt_source_url,
                exc_info=True,
            )
            scraped = self._scraper.scrape_for_date(source_url=self._scraper.source_url, target_date=effective_date)
            return self._persist_scraped(original=scraped, pt_scraped=None, force_refresh=force_refresh)

        try:
            es_scraped = self._scraper.scrape_for_date(source_url=self._scraper.source_url, target_date=effective_date)
        except Exception:
            logger.warning(
                "Meditação em português obtida com sucesso, mas a raspagem da versão em espanhol (%s) falhou. "
                "Os campos originais usarão o texto em português como cópia.",
                self._scraper.source_url,
                exc_info=True,
            )
            es_scraped = pt_scraped

        return self._persist_scraped(original=es_scraped, pt_scraped=pt_scraped, force_refresh=force_refresh)

    def scrape_and_store_pt_only(
        self,
        source_url: str,
        target_date: datetime | None = None,
        force_refresh: bool = False,
    ) -> tuple[Meditacao, bool]:
        """Rasp a `source_url` e atualiza somente os campos `_pt`, preservando o
        conteúdo em espanhol já salvo. Se ainda não existir registro para a data,
        cria um novo raspando também a fonte em espanhol normalmente."""
        effective_date = target_date or datetime.now(ZoneInfo("America/Sao_Paulo"))
        pt_scraped = self._scraper.scrape_for_date(source_url=source_url, target_date=effective_date)

        existing = self._db.scalar(select(Meditacao).where(Meditacao.data == pt_scraped.data))
        if existing is None:
            es_scraped = self._scraper.scrape_for_date(
                source_url=self._scraper.source_url, target_date=effective_date
            )
            return self._persist_scraped(original=es_scraped, pt_scraped=pt_scraped, force_refresh=True)

        if not force_refresh:
            return existing, False

        existing.leitura_ref_pt = pt_scraped.leitura_ref
        existing.titulo_pt = pt_scraped.titulo
        existing.subtitulo_pt = pt_scraped.subtitulo
        existing.conteudo_i_pt = pt_scraped.conteudo_i
        existing.conteudo_ii_pt = pt_scraped.conteudo_ii
        existing.conteudo_iii_pt = pt_scraped.conteudo_iii
        existing.fonte_traducao = "site_pt"
        self._db.commit()
        self._db.refresh(existing)
        logger.info("Meditação (somente PT) atualizada com sucesso para a data %s.", existing.data)
        return existing, True

    def scrape_and_store_es_only(
        self,
        source_url: str,
        target_date: datetime | None = None,
        force_refresh: bool = False,
    ) -> tuple[Meditacao, bool]:
        """Rasp a `source_url` e atualiza somente os campos em espanhol (originais),
        preservando o conteúdo em português já salvo. Se ainda não existir registro
        para a data, cria um novo traduzindo o conteúdo raspado para português."""
        effective_date = target_date or datetime.now(ZoneInfo("America/Sao_Paulo"))
        es_scraped = self._scraper.scrape_for_date(source_url=source_url, target_date=effective_date)

        existing = self._db.scalar(select(Meditacao).where(Meditacao.data == es_scraped.data))
        if existing is None:
            return self._persist_scraped(original=es_scraped, pt_scraped=None, force_refresh=True)

        if not force_refresh:
            return existing, False

        existing.titulo_raw = es_scraped.titulo_raw
        existing.titulo = es_scraped.titulo
        existing.subtitulo_raw = es_scraped.subtitulo_raw
        existing.subtitulo = es_scraped.subtitulo
        existing.leitura_ref_raw = es_scraped.leitura_ref_raw
        existing.leitura_ref = es_scraped.leitura_ref
        existing.conteudo_i_raw = es_scraped.conteudo_i_raw
        existing.conteudo_i = es_scraped.conteudo_i
        existing.conteudo_ii_raw = es_scraped.conteudo_ii_raw
        existing.conteudo_ii = es_scraped.conteudo_ii
        existing.conteudo_iii_raw = es_scraped.conteudo_iii_raw
        existing.conteudo_iii = es_scraped.conteudo_iii
        self._db.commit()
        self._db.refresh(existing)
        logger.info("Meditação (somente ES) atualizada com sucesso para a data %s.", existing.data)
        return existing, True

    def _persist_scraped(
        self,
        original: ScrapedMeditation,
        pt_scraped: ScrapedMeditation | None,
        force_refresh: bool,
    ) -> tuple[Meditacao, bool]:
        existing = self._db.scalar(select(Meditacao).where(Meditacao.data == original.data))
        if existing is not None and not force_refresh:
            return existing, False

        payload = asdict(original)
        if pt_scraped is not None:
            payload["leitura_ref_pt"] = pt_scraped.leitura_ref
            payload["titulo_pt"] = pt_scraped.titulo
            payload["subtitulo_pt"] = pt_scraped.subtitulo
            payload["conteudo_i_pt"] = pt_scraped.conteudo_i
            payload["conteudo_ii_pt"] = pt_scraped.conteudo_ii
            payload["conteudo_iii_pt"] = pt_scraped.conteudo_iii
            payload["fonte_traducao"] = "site_pt"
        else:
            payload["leitura_ref_pt"] = _norm(_translate_or_empty(self._translator, original.leitura_ref))
            payload["titulo_pt"] = _norm(_translate_or_empty(self._translator, original.titulo))
            payload["subtitulo_pt"] = _norm(_translate_or_empty(self._translator, original.subtitulo))
            payload["conteudo_i_pt"] = _norm(_translate_or_empty(self._translator, original.conteudo_i))
            payload["conteudo_ii_pt"] = _norm(_translate_or_empty(self._translator, original.conteudo_ii))
            payload["conteudo_iii_pt"] = _norm(_translate_or_empty(self._translator, original.conteudo_iii))
            payload["fonte_traducao"] = self._translator.source

        meditacao_create = MeditacaoCreate(**payload)
        if existing is not None:
            for key, value in meditacao_create.model_dump().items():
                setattr(existing, key, value)
            meditation = existing
        else:
            meditation = Meditacao(**meditacao_create.model_dump())
            self._db.add(meditation)

        self._db.commit()
        self._db.refresh(meditation)
        logger.info("Meditação salva com sucesso para a data %s.", meditation.data)
        return meditation, True

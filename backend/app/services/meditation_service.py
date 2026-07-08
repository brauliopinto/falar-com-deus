import logging
from dataclasses import asdict
from datetime import datetime
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
            should_translate = translate if translate is not None else True
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

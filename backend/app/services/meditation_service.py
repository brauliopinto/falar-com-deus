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
    return translator.translate_es_to_pt(text)


class MeditationService:
    def __init__(self, db: Session, scraper: ScraperService, translator: TranslatorService) -> None:
        self._db = db
        self._scraper = scraper
        self._translator = translator

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
    ) -> tuple[Meditacao, bool]:
        scraped = self._scraper.scrape_for_date(source_url=source_url, target_date=target_date)
        return self._persist_scraped(scraped=scraped, force_refresh=force_refresh)

    def _persist_scraped(
        self,
        scraped: ScrapedMeditation,
        force_refresh: bool,
    ) -> tuple[Meditacao, bool]:
        existing = self._db.scalar(select(Meditacao).where(Meditacao.data == scraped.data))
        if existing is not None and not force_refresh:
            return existing, False

        payload = asdict(scraped)
        payload["leitura_ref_pt"] = _norm(_translate_or_empty(self._translator, scraped.leitura_ref))
        payload["titulo_pt"] = _norm(_translate_or_empty(self._translator, scraped.titulo))
        payload["subtitulo_pt"] = _norm(_translate_or_empty(self._translator, scraped.subtitulo))
        payload["conteudo_i_pt"] = _norm(_translate_or_empty(self._translator, scraped.conteudo_i))
        payload["conteudo_ii_pt"] = _norm(_translate_or_empty(self._translator, scraped.conteudo_ii))
        payload["conteudo_iii_pt"] = _norm(_translate_or_empty(self._translator, scraped.conteudo_iii))
        payload["fonte_traducao"] = "deepl"

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

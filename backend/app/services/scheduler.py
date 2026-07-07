import logging

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.session import SessionLocal
from app.services.meditation_service import MeditationService
from app.services.scraper import ScraperService
from app.services.translator import TranslatorService

logger = logging.getLogger(__name__)


class ScrapeScheduler:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._scheduler = BackgroundScheduler(timezone=settings.timezone)

    # Tentativas adicionais deslocadas em +3h e +6h em relação ao horário base
    _RETRY_OFFSETS_HOURS = [0, 3, 6]

    def start(self) -> None:
        base_hour = self._settings.scrape_schedule_hour
        base_minute = self._settings.scrape_schedule_minute

        for attempt, offset in enumerate(self._RETRY_OFFSETS_HOURS, start=1):
            hour = (base_hour + offset) % 24
            self._scheduler.add_job(
                func=self._run_daily_scrape,
                kwargs={"attempt": attempt},
                trigger=CronTrigger(hour=hour, minute=base_minute),
                id=f"daily_meditation_scrape_{attempt}",
                replace_existing=True,
            )

        self._scheduler.start()
        base = self._settings.scrape_schedule_hour
        m = self._settings.scrape_schedule_minute
        logger.info(
            "Raspagem agendada em 3 tentativas: %02d:%02d, %02d:%02d, %02d:%02d (%s).",
            base % 24, m,
            (base + 3) % 24, m,
            (base + 6) % 24, m,
            self._settings.timezone,
        )

    def shutdown(self) -> None:
        self._scheduler.shutdown(wait=False)

    def _run_daily_scrape(self, attempt: int = 1) -> None:
        logger.info("Iniciando raspagem diária (tentativa %d/3).", attempt)
        db: Session = SessionLocal()
        try:
            service = MeditationService(
                db=db,
                scraper=ScraperService(self._settings.scrape_source_url),
                translator=TranslatorService(
                    openrouter_api_key=self._settings.openrouter_api_key,
                    llm_model=self._settings.llm_model,
                    deepl_api_key=self._settings.deepl_api_key,
                ),
            )
            _, created = service.scrape_and_store_today()
            if created:
                logger.info("Tentativa %d/3: nova meditação salva com sucesso.", attempt)
            else:
                logger.info("Tentativa %d/3: meditação já existente, nenhuma ação necessária.", attempt)
        except Exception:
            logger.exception("Tentativa %d/3: falha na raspagem diária.", attempt)
            raise
        finally:
            db.close()

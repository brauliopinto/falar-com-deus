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

    def start(self) -> None:
        self._scheduler.add_job(
            func=self._run_daily_scrape,
            trigger=CronTrigger(
                hour=self._settings.scrape_schedule_hour,
                minute=self._settings.scrape_schedule_minute,
            ),
            id="daily_meditation_scrape",
            replace_existing=True,
        )
        self._scheduler.start()
        logger.info(
            "Agendamento diário de raspagem configurado para %02d:%02d (%s).",
            self._settings.scrape_schedule_hour,
            self._settings.scrape_schedule_minute,
            self._settings.timezone,
        )

    def shutdown(self) -> None:
        self._scheduler.shutdown(wait=False)

    def _run_daily_scrape(self) -> None:
        logger.info("Iniciando job agendado de raspagem diária.")
        db: Session = SessionLocal()
        try:
            service = MeditationService(
                db=db,
                scraper=ScraperService(self._settings.scrape_source_url),
                translator=TranslatorService(self._settings.deepl_api_key),
            )
            _, created = service.scrape_and_store_today()
            if created:
                logger.info("Job diário concluído com nova meditação salva.")
            else:
                logger.info("Job diário concluído sem inserção (registro já existente).")
        except Exception:
            logger.exception("Falha no job de raspagem diária.")
            raise
        finally:
            db.close()

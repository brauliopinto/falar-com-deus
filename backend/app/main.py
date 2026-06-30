from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.meditacoes import router as meditacoes_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.services.scheduler import ScrapeScheduler

setup_logging()
settings = get_settings()
scheduler = ScrapeScheduler(settings=settings)


@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler.start()
    try:
        yield
    finally:
        scheduler.shutdown()


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(meditacoes_router)


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}

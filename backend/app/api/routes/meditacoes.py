from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import require_scrape_api_key
from app.db.session import get_db
from app.schemas.meditacao import MeditacaoListResponse, MeditacaoResponse, ScrapeResponse
from app.services.meditation_service import MeditationService
from app.services.scraper import ScraperService
from app.services.translator import TranslatorService

router = APIRouter(prefix="/meditacoes", tags=["Meditações"])


def _service(db: Session) -> MeditationService:
    settings = get_settings()
    return MeditationService(
        db=db,
        scraper=ScraperService(settings.scrape_source_url),
        translator=TranslatorService(
            openrouter_api_key=settings.openrouter_api_key,
            llm_model=settings.llm_model,
            deepl_api_key=settings.deepl_api_key,
        ),
        pt_source_url=settings.scrape_source_url_pt,
    )


def _to_response(item) -> MeditacaoResponse:
    return MeditacaoResponse.model_validate(item)


@router.get("/hoje", response_model=MeditacaoResponse)
def get_meditacao_hoje(db: Session = Depends(get_db)) -> MeditacaoResponse:
    meditation = _service(db).get_today()
    return _to_response(meditation)


@router.get("/por-data", response_model=MeditacaoResponse)
def get_meditacao_por_data(
    data: str = Query(..., pattern=r"^\d{2}/\d{2}/\d{4}$"),
    db: Session = Depends(get_db),
) -> MeditacaoResponse:
    meditation = _service(db).get_by_date(data)
    return _to_response(meditation)


@router.get("/", response_model=MeditacaoListResponse)
def list_meditacoes(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> MeditacaoListResponse:
    items, total = _service(db).list_all(limit=limit, offset=offset)
    return MeditacaoListResponse(
        items=[_to_response(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/raspar", response_model=ScrapeResponse, dependencies=[Depends(require_scrape_api_key)])
def raspar_meditacao(
    force: bool = Query(default=False),
    source_url: str | None = Query(default=None),
    translate: bool | None = Query(
        default=None,
        description=(
            "Válido apenas junto com source_url. Se True (padrão), o conteúdo raspado é traduzido "
            "via LLM/DeepL (assume fonte em espanhol). Se False, o conteúdo raspado é salvo direto "
            "como português, sem tradução (use para reraspar uma URL que já está em português)."
        ),
    ),
    date: str | None = Query(default=None, pattern=r"^\d{2}/\d{2}/\d{4}$"),
    db: Session = Depends(get_db),
) -> ScrapeResponse:
    target_date: datetime | None = None
    if date is not None:
        target_date = datetime.strptime(date, "%d/%m/%Y")
    meditation, changed = _service(db).scrape_and_store_today(
        force_refresh=force, source_url=source_url, target_date=target_date, translate=translate
    )
    if changed and force:
        message = "Raspagem concluída e registro existente foi atualizado."
        status = "updated"
    elif changed:
        message = "Raspagem concluída e registro salvo."
        status = "created"
    else:
        message = "Registro já existia. Nenhuma nova inserção foi feita."
        status = "skipped"
    return ScrapeResponse(status=status, data=meditation.data, message=message)

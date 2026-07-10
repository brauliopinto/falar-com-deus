from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
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
            "Válido apenas junto com source_url. Se omitido, é inferido automaticamente pela URL "
            "(URLs com '/pt/' não são traduzidas; as demais são tratadas como espanhol e traduzidas). "
            "Se True, força tradução via LLM/DeepL (assume fonte em espanhol). Se False, força salvar "
            "o conteúdo raspado direto como português, sem tradução."
        ),
    ),
    pt_only: bool = Query(
        default=False,
        description=(
            "Válido apenas junto com source_url. Se True, atualiza somente os campos em português "
            "com o conteúdo raspado, preservando o conteúdo em espanhol já salvo para a data (ou "
            "raspando a fonte em espanhol normalmente se ainda não existir registro para a data). "
            "Mutuamente exclusivo com es_only."
        ),
    ),
    es_only: bool = Query(
        default=False,
        description=(
            "Válido apenas junto com source_url. Se True, atualiza somente os campos em espanhol "
            "com o conteúdo raspado, preservando o conteúdo em português já salvo para a data (ou "
            "traduzindo o conteúdo raspado para português se ainda não existir registro para a data). "
            "Mutuamente exclusivo com pt_only."
        ),
    ),
    date: str | None = Query(default=None, pattern=r"^\d{2}/\d{2}/\d{4}$"),
    db: Session = Depends(get_db),
) -> ScrapeResponse:
    if pt_only and es_only:
        raise HTTPException(status_code=400, detail="pt_only e es_only são mutuamente exclusivos.")
    if (pt_only or es_only) and source_url is None:
        raise HTTPException(status_code=400, detail="pt_only/es_only requer source_url.")

    target_date: datetime | None = None
    if date is not None:
        target_date = datetime.strptime(date, "%d/%m/%Y")

    service = _service(db)
    if pt_only:
        meditation, changed = service.scrape_and_store_pt_only(
            source_url=source_url, target_date=target_date, force_refresh=force
        )
    elif es_only:
        meditation, changed = service.scrape_and_store_es_only(
            source_url=source_url, target_date=target_date, force_refresh=force
        )
    else:
        meditation, changed = service.scrape_and_store_today(
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

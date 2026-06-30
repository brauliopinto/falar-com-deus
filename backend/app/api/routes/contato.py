import logging

from fastapi import APIRouter, HTTPException, status

from app.core.config import get_settings
from app.schemas.contato import ContatoRequest, ContatoResponse
from app.services.email_service import EmailService

router = APIRouter(prefix="/contato", tags=["Contato"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=ContatoResponse)
def enviar_contato(request: ContatoRequest) -> ContatoResponse:
    settings = get_settings()
    try:
        EmailService(settings).send_contact(
            nome=request.nome,
            email=request.email,
            assunto=request.assunto,
            mensagem=request.mensagem,
        )
    except Exception:
        logger.exception("Falha ao enviar e-mail de contato.")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Não foi possível enviar a mensagem. Tente novamente em instantes.",
        )
    return ContatoResponse(status="ok", message="Mensagem enviada com sucesso.")

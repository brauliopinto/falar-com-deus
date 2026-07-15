import logging
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import Settings

logger = logging.getLogger(__name__)

_HEADER_CONTROL_CHARS = re.compile(r"[\r\n]")


def _sanitize_header_value(value: str) -> str:
    return _HEADER_CONTROL_CHARS.sub(" ", value).strip()


class EmailService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def send_contact(self, nome: str, email: str, assunto: str, mensagem: str) -> None:
        msg = MIMEMultipart()
        msg["From"] = self._settings.smtp_user
        msg["To"] = self._settings.contact_email
        msg["Subject"] = f"[FALAR COM DEUS] {_sanitize_header_value(assunto)}"
        msg["Reply-To"] = _sanitize_header_value(email)

        body = f"Nome: {nome}\nE-mail: {email}\n\n{mensagem}"
        msg.attach(MIMEText(body, "plain", "utf-8"))

        with smtplib.SMTP(self._settings.smtp_host, self._settings.smtp_port) as server:
            server.ehlo()
            server.starttls()
            server.login(self._settings.smtp_user, self._settings.smtp_password)
            server.send_message(msg)

        logger.info("Mensagem de contato enviada de %s para %s.", email, self._settings.contact_email)

from fastapi import Header, HTTPException, status

from app.core.config import get_settings


def require_scrape_api_key(x_api_key: str = Header(default="", alias="X-API-Key")) -> None:
    settings = get_settings()
    provided_key = x_api_key.strip()
    expected_key = settings.scrape_api_key.strip()
    if not provided_key or provided_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-API-Key inválida.",
        )

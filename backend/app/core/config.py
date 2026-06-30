from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Meditação Diária API"
    ambiente: str = Field(default="development", alias="AMBIENTE")
    database_url: str = Field(alias="DATABASE_URL")
    deepl_api_key: str = Field(alias="DEEPL_API_KEY")
    scrape_api_key: str = Field(alias="SCRAPE_API_KEY")
    scrape_source_url: str = Field(
        default="https://hablarcondios.org/meditacion-diaria/",
        alias="SCRAPE_SOURCE_URL",
    )
    scrape_schedule_hour: int = Field(default=6, alias="SCRAPE_SCHEDULE_HOUR")
    scrape_schedule_minute: int = Field(default=0, alias="SCRAPE_SCHEDULE_MINUTE")
    timezone: str = Field(default="America/Sao_Paulo", alias="TIMEZONE")
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "https://localhost:3000"],
        alias="CORS_ORIGINS",
    )
    smtp_host: str = Field(default="smtp.gmail.com", alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str = Field(alias="SMTP_USER")
    smtp_password: str = Field(alias="SMTP_PASSWORD")
    contact_email: str = Field(alias="CONTACT_EMAIL")


@lru_cache
def get_settings() -> Settings:
    return Settings()

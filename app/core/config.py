"""SALEP core configuration. Loads from environment variables."""

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")

    google_sheets_id: str = Field(default="", alias="GOOGLE_SHEETS_ID")
    google_service_account_json: str = Field(
        default="service-account.json",
        alias="GOOGLE_SERVICE_ACCOUNT_JSON",
    )

    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


settings = Settings()

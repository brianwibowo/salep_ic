"""SALEP core configuration. Loads from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # LLM Provider selection: "gemini" | "groq" | "openai" | "openrouter" | "ollama" | "custom"
    llm_provider: str = Field(default="", alias="LLM_PROVIDER")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_base_url: str = Field(default="", alias="LLM_BASE_URL")
    llm_model: str = Field(default="", alias="LLM_MODEL")

    # Specific Provider Keys
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")
    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    openrouter_api_key: str = Field(default="", alias="OPENROUTER_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")

    # Google Sheets
    google_sheets_id: str = Field(default="", alias="GOOGLE_SHEETS_ID")
    google_service_account_json: str = Field(
        default="service-account.json",
        alias="GOOGLE_SERVICE_ACCOUNT_JSON",
    )

    # Apify Data Ingestion (Threads & LinkedIn)
    apify_api_token: str = Field(default="", alias="APIFY_API_TOKEN")
    threads_actor_id: str = Field(
        default="igview-owner~threads-search-scraper",
        alias="THREADS_ACTOR_ID",
    )
    linkedin_actor_id: str = Field(
        default="harvestapi~linkedin-post-search",
        alias="LINKEDIN_ACTOR_ID",
    )

    # Automated Background Scheduler
    auto_search_enabled: bool = Field(default=True, alias="AUTO_SEARCH_ENABLED")
    auto_search_interval_minutes: int = Field(default=15, alias="AUTO_SEARCH_INTERVAL_MINUTES")
    auto_search_keywords: str = Field(
        default="buatkan website,bikin website,butuh website,jasa website,rekomendasi software house,butuh vendor IT,cari programmer,jasa landing page",
        alias="AUTO_SEARCH_KEYWORDS",
    )
    auto_search_sources: str = Field(default="threads,linkedin", alias="AUTO_SEARCH_SOURCES")
    auto_search_limit_per_run: int = Field(default=5, alias="AUTO_SEARCH_LIMIT_PER_RUN")

    # App
    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def active_llm_provider(self) -> str:
        """Auto-detect or return explicit LLM provider."""
        if self.llm_provider:
            return self.llm_provider.lower().strip()
        if self.gemini_api_key:
            return "gemini"
        if self.groq_api_key:
            return "groq"
        if self.openrouter_api_key:
            return "openrouter"
        if self.openai_api_key:
            return "openai"
        return "gemini"  # Default recommended free provider

    @property
    def active_llm_key(self) -> str:
        """Get the API key for the active provider."""
        if self.llm_api_key:
            return self.llm_api_key
        prov = self.active_llm_provider
        if prov == "gemini":
            return self.gemini_api_key
        elif prov == "groq":
            return self.groq_api_key
        elif prov == "openrouter":
            return self.openrouter_api_key
        elif prov == "openai":
            return self.openai_api_key
        elif prov == "ollama":
            return "ollama"
        return ""

    @property
    def active_llm_base_url(self) -> str | None:
        """Get the base URL for the active provider."""
        if self.llm_base_url:
            return self.llm_base_url
        prov = self.active_llm_provider
        if prov == "gemini":
            # Google AI Studio official OpenAI-compatible endpoint
            return "https://generativelanguage.googleapis.com/v1beta/openai/"
        elif prov == "groq":
            return "https://api.groq.com/openai/v1"
        elif prov == "openrouter":
            return "https://openrouter.ai/api/v1"
        elif prov == "ollama":
            return "http://localhost:11434/v1"
        elif prov == "openai":
            return None  # Default OpenAI client base
        return None

    @property
    def active_llm_model(self) -> str:
        """Get the model name for the active provider."""
        if self.llm_model:
            return self.llm_model
        prov = self.active_llm_provider
        if prov == "gemini":
            return "gemini-3.5-flash"
        elif prov == "groq":
            return "llama-3.3-70b-versatile"
        elif prov == "openrouter":
            return "google/gemini-2.0-flash-exp:free"
        elif prov == "ollama":
            return "qwen2.5:7b"
        elif prov == "openai":
            return self.openai_model or "gpt-4o-mini"
        return "gemini-3.8-flash"


settings = Settings()

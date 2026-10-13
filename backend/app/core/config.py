"""SALEP core configuration. Loads from environment variables."""

from __future__ import annotations

from pydantic_settings import BaseSettings
from pydantic import Field
from urllib.parse import urlparse


class Settings(BaseSettings):
    # Runtime role. API instances should be stateless; the worker owns the
    # periodic scheduler in production.
    process_role: str = Field(default="api", alias="SALEP_PROCESS_ROLE")

    # Persistence. Leave DATABASE_URL empty to keep the local SQLite adapter.
    # Production should set a PostgreSQL URL and run `alembic upgrade head`.
    database_url: str = Field(default="", alias="DATABASE_URL")
    database_auto_create: bool = Field(default=False, alias="DATABASE_AUTO_CREATE")
    auth_database_url: str = Field(default="", alias="AUTH_DATABASE_URL")
    auth_session_ttl_seconds: int = Field(default=28800, ge=300, le=86400, alias="AUTH_SESSION_TTL_SECONDS")
    auth_login_window_seconds: int = Field(default=900, ge=60, le=3600, alias="AUTH_LOGIN_WINDOW_SECONDS")
    auth_login_account_limit: int = Field(default=10, ge=3, le=100, alias="AUTH_LOGIN_ACCOUNT_LIMIT")
    auth_login_ip_limit: int = Field(default=100, ge=10, le=1000, alias="AUTH_LOGIN_IP_LIMIT")

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
    auto_search_interval_minutes: int = Field(default=30, ge=1, alias="AUTO_SEARCH_INTERVAL_MINUTES")
    auto_search_keywords: str = Field(
        default="butuh website,rekomendasi hosting,butuh server VPS,cari managed service,butuh software house,migrasi cloud,vendor jaringan kantor,jasa pentest,solusi backup data,implementasi ERP,rekomendasi CRM,butuh aplikasi mobile,otomatisasi bisnis,konsultan IT,monitoring server,integrasi API",
        alias="AUTO_SEARCH_KEYWORDS",
    )
    auto_search_sources: str = Field(default="threads", alias="AUTO_SEARCH_SOURCES")
    auto_search_limit_per_run: int = Field(default=5, alias="AUTO_SEARCH_LIMIT_PER_RUN")

    # Inaproc procurement sync (two-year rolling window, every scheduler cycle)
    inaproc_auto_sync_enabled: bool = Field(default=True, alias="INAPROC_AUTO_SYNC_ENABLED")
    inaproc_sync_limit: int = Field(default=500, ge=1, le=5000, alias="INAPROC_SYNC_LIMIT")

    # App
    app_env: str = Field(default="development", alias="APP_ENV")
    app_domain: str = Field(default="salep1.duckdns.org", alias="APP_DOMAIN")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Operational hardening
    scheduler_lock_name: str = Field(default="salep-discovery-scheduler", alias="SCHEDULER_LOCK_NAME")
    scheduler_lock_path: str = Field(default="data/salep-scheduler.lock", alias="SCHEDULER_LOCK_PATH")
    retry_max_attempts: int = Field(default=3, ge=1, le=8, alias="RETRY_MAX_ATTEMPTS")
    retry_base_delay_seconds: float = Field(default=1.0, ge=0.1, le=60.0, alias="RETRY_BASE_DELAY_SECONDS")
    circuit_failure_threshold: int = Field(default=3, ge=1, le=20, alias="CIRCUIT_FAILURE_THRESHOLD")
    circuit_recovery_seconds: int = Field(default=120, ge=10, le=3600, alias="CIRCUIT_RECOVERY_SECONDS")
    alert_webhook_url: str = Field(default="", alias="ALERT_WEBHOOK_URL")
    alert_cooldown_seconds: int = Field(default=900, ge=0, le=86400, alias="ALERT_COOLDOWN_SECONDS")
    backup_dir: str = Field(default="data/backups", alias="BACKUP_DIR")
    backup_retention_days: int = Field(default=14, ge=1, le=3650, alias="BACKUP_RETENTION_DAYS")
    snapshot_retention_days: int = Field(default=90, ge=1, le=3650, alias="SNAPSHOT_RETENTION_DAYS")

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def app_base_url(self) -> str:
        """Production public URL or localhost in development."""
        if self.is_production:
            domain = self.app_domain.strip().rstrip("/")
            if not domain.startswith(("http://", "https://")):
                domain = f"https://{domain}"
            return domain
        return "http://localhost:8000"

    @property
    def cors_origins(self) -> list[str]:
        """CORS allowed origins for production domain and local dev."""
        configured = self.app_domain.strip().rstrip("/")
        if configured.startswith(("http://", "https://")):
            parsed = urlparse(configured)
            domain = parsed.netloc
            configured_origin = configured
        else:
            domain = configured
            configured_origin = f"https://{domain}"
        if self.is_production:
            return [configured_origin]
        origins = [
            configured_origin,
            f"http://{domain}",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
        return list(dict.fromkeys(origins))

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

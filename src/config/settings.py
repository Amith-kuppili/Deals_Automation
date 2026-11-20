from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, model_validator


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = Field(default="postgresql+asyncpg://postgres:postgres@db:5432/deal_hunter")

    # Redis
    REDIS_URL: str = Field(default="redis://redis:6379/0")

    # Celery
    CELERY_BROKER_URL: str = Field(default="redis://redis:6379/0")
    CELERY_RESULT_BACKEND: str = Field(default="redis://redis:6379/0")

    # API
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8000)

    # E-Commerce API Configuration (Generic)
    ECOMMERCE_API_ENABLED: bool = Field(default=False)
    ECOMMERCE_API_BASE_URL: str = Field(default="https://api.quickcommerce.io/v1")
    ECOMMERCE_API_KEY: str = Field(default="")
    ECOMMERCE_API_TIMEOUT_SECONDS: int = Field(default=30)
    ECOMMERCE_API_MAX_RETRIES: int = Field(default=3)
    ECOMMERCE_API_MIN_CREDITS: int = Field(default=5)
    ECOMMERCE_API_LOW_CREDITS_THRESHOLD: int = Field(default=10)

    # Amazon Providers
    AMAZON_ENABLED: bool = Field(default=False)
    AMAZON_PRIMARY_PROVIDER: str = Field(default="openwebninja")
    AMAZON_BACKUP_PROVIDER: str = Field(default="brightdata")
    # Amazon marketplace country (US, IN, GB, DE, ...), also drives currency.
    AMAZON_COUNTRY: str = Field(default="IN")

    # OpenWeb Ninja
    OPENWEBNINJA_ENABLED: bool = Field(default=False)
    OPENWEBNINJA_API_KEY: str = Field(default="")
    OPENWEBNINJA_BASE_URL: str = Field(
        default="https://api.openwebninja.com/realtime-amazon-data"
    )
    OPENWEBNINJA_TIMEOUT_SECONDS: int = Field(default=30)
    OPENWEBNINJA_MAX_RETRIES: int = Field(default=3)
    OPENWEBNINJA_MONTHLY_REQUEST_LIMIT: int = Field(default=100)
    OPENWEBNINJA_LOW_REQUEST_THRESHOLD: int = Field(default=10)

    # Bright Data
    BRIGHTDATA_ENABLED: bool = Field(default=False)
    BRIGHTDATA_API_KEY: str = Field(default="")
    BRIGHTDATA_BASE_URL: str = Field(default="https://api.brightdata.com")
    BRIGHTDATA_TIMEOUT_SECONDS: int = Field(default=30)
    BRIGHTDATA_MAX_RETRIES: int = Field(default=3)

    # Other Providers
    AMAZON_CLIENT_ID: str = Field(default="")
    AMAZON_CLIENT_SECRET: str = Field(default="")
    AMAZON_REFRESH_TOKEN: str = Field(default="")

    # Notifications
    TELEGRAM_BOT_TOKEN: str = Field(default="")
    TELEGRAM_CHAT_ID: str = Field(default="")

    # Flipkart Affiliate API
    FLIPKART_ENABLED: bool = Field(default=False)
    FLIPKART_API_TOKEN: str = Field(default="")
    FLIPKART_TRACKING_ID: str = Field(default="")
    FLIPKART_CATEGORIES: str = Field(default="electronics,mobiles,computers")
    FLIPKART_SYNC_INTERVAL_MINUTES: int = Field(default=60, ge=1)
    FLIPKART_TIMEOUT_SECONDS: int = Field(default=30)
    FLIPKART_MAX_RETRIES: int = Field(default=3)

    # Deal Engine
    DEAL_MIN_HISTORY_OBSERVATIONS: int = Field(default=5)
    DEAL_HIGH_CONFIDENCE_HISTORY_OBSERVATIONS: int = Field(default=20)
    DEAL_HISTORY_WINDOW_DAYS: int = Field(default=30)

    # ReefAPI
    REEFAPI_ENABLED: bool = Field(default=False)
    REEFAPI_API_KEY: str = Field(default="")
    REEFAPI_BASE_URL: str = Field(default="")
    REEFAPI_TIMEOUT_SECONDS: int = Field(default=30)
    REEFAPI_MAX_RETRIES: int = Field(default=3)
    REEFAPI_BOOTSTRAP_ENABLED: bool = Field(default=False)
    REEFAPI_BOOTSTRAP_COOLDOWN_HOURS: int = Field(default=24)
    REEFAPI_LOW_CREDITS_THRESHOLD: int = Field(default=100)

    @field_validator("*", mode="before")
    @classmethod
    def _strip_string_values(cls, value):
        """Strip stray whitespace/CR from env values (e.g. CRLF lines in .env)."""
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, value):
        url = str(value).strip()
        if url.startswith("postgres://"):
            return "postgresql+asyncpg://" + url[len("postgres://"):]
        if url.startswith("postgresql://"):
            return "postgresql+asyncpg://" + url[len("postgresql://"):]
        return url

    @model_validator(mode="after")
    def sync_railway_redis_urls(self):
        """Use REDIS_URL for Celery unless a broker URL was explicitly supplied."""
        default_local_url = "redis://redis:6379/0"
        if self.CELERY_BROKER_URL == default_local_url:
            self.CELERY_BROKER_URL = self.REDIS_URL
        if self.CELERY_RESULT_BACKEND == default_local_url:
            self.CELERY_RESULT_BACKEND = self.REDIS_URL
        return self

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

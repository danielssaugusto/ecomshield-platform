from secrets import token_urlsafe

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "EcomShield API"

    # Database
    DATABASE_URL: str = "postgresql://ecomshield:ecomshield_dev@localhost:5432/ecomshield"

    # JWT / Auth
    SECRET_KEY: str = Field(default_factory=lambda: token_urlsafe(48))
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ADMIN_BOOTSTRAP_PASSWORD: str | None = None

    # CORS
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

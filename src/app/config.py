from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "EcomShield API"

    # Database
    DATABASE_URL: str = "postgresql://ecomshield:ecomshield_dev@localhost:5432/ecomshield"

    # JWT / Auth
    SECRET_KEY: str = "chave_dev_temporaria_altere_no_arquivo_env"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
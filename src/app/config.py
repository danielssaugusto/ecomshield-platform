from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "EcomShield API"

    # Database
    DATABASE_URL: str = "postgresql://ecomshield:ecomshield_dev@localhost:5432/ecomshield"

    # JWT / Auth
    SECRET_KEY: str = "chave_dev_temporaria_altere_no_arquivo_env"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

<<<<<<< HEAD
    # CORS
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]

=======
>>>>>>> b6eb3ce935a1d7d0e6a23984cb49ca4a7766ae87
    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
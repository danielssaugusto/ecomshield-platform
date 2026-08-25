from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "EcomShield API"

    SECRET_KEY: str = "chave_dev_temporaria_altere_no_arquivo_env"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"


settings = Settings()
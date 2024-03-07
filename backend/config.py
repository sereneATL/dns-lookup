import pathlib
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    API_V1_STR: str = "v1"
    VERSION: str = "0.1.0"
    PROJECT_NAME: str = "DNS lookup system"
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_URL: str = 'host.docker.internal:5432'
    KUBERNETES: bool = False

    model_config = SettingsConfigDict(env_file=f"{pathlib.Path(__file__).resolve().parent}/.env")

settings = Settings()

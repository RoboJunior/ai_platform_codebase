from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


# All the env values are stored into this settings.
class Settings(BaseSettings):
    DATABASE_NAME: str
    TEMPORAL_URL: str
    SENDER_EMAIL: str
    SENDER_PASSWORD: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRY_MINUTES: int

    model_config = SettingsConfigDict(env_file=".env")

# All the configuration goes here.
class Config:
    DB_CONFIG = "sqlite:///{}.db"

@lru_cache
def get_settings():
    return Settings()
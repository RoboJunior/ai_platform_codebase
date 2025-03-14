from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


# All the env values are stored into this settings.
class Settings(BaseSettings):
    DATABASE_NAME: str
    TEMPORAL_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRY_MINUTES: int
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_FROM_NAME: str
    MAIL_PORT: int
    MAIL_SERVER:str
    MAIL_STARTTLS: bool = False
    MAIL_SSL_TLS: bool = True
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True
    DOMAIN: str
    REDIS_HOST: str
    REDIS_PORT: int
    
    model_config = SettingsConfigDict(env_file=".env")

# All the configuration goes here.
class Config:
    DB_CONFIG = "sqlite:///{}.db"

@lru_cache
def get_settings():
    return Settings()
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    postgres_url: str
    redis_url: str
    pipecat_api_key: str
    pipecat_api_endpoint: str
    pubsub_channel: str = "magic-mirror-events"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()

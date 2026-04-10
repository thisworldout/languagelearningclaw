from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://lluser:llpass@localhost:5432/languagelearning"
    api_key: str = "dev-insecure-change-me"

    openai_api_key: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"

    elevenlabs_api_key: str | None = None
    elevenlabs_voice_id: str | None = None

    whisper_model: str = "whisper-1"

    # ClawMetry / observability (documented for OpenClaw host env)
    clawmetry_enabled: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()

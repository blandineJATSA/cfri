from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_env: str = "development"
    app_secret_key: str = "change-me"
    frontend_url: str = "http://localhost:3000"
    database_url: str
    redis_url: str = "redis://localhost:6379"
    openai_api_key: str = ""
    ai_model: str = "gpt-4o-mini"
    clerk_secret_key: str = ""
    clerk_jwks_url: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
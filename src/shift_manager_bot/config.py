from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # Bot
    bot_token: str

    # Database
    db_host: str
    db_port: int = 5432
    db_user: str
    db_pass: str
    db_name: str

    # Redis
    redis_host: str
    redis_port: int = 6379

    # App
    secret_key: str
    debug: bool = False

    # Test
    test_db_url: str

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_pass}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # pyright: ignore


settings = get_settings()

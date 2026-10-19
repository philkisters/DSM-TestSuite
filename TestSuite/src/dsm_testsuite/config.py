from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Environment variables take precedence over values in TestSuite/.env."""

    model_config = SettingsConfigDict(env_file=PROJECT_DIR / ".env", extra="ignore")

    database_url: str = ""
    proxy_admin_url: str = "http://localhost:8080"
    http_timeout: float = 10.0
    host: str = "0.0.0.0"
    port: int = 8000
    challenges_dir: str = str(PROJECT_DIR / "Challenges")


settings = Settings()

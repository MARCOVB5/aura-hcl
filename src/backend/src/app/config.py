from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# src/backend/.env, written by db/init_bd.sh. Real environment variables take precedence over it.
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

class Settings(BaseSettings):
  model_config = SettingsConfigDict(env_file = ENV_FILE)

  database_url : str

settings = Settings()

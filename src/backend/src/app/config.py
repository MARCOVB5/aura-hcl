from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# src/backend/.env, written by db/init_bd.sh. Real environment variables take precedence over it.
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

class Settings(BaseSettings):
  model_config = SettingsConfigDict(env_file = ENV_FILE)

  database_url : str
  # origins allowed to call the API from a browser (the Vite dev server by default).
  # to override, set CORS_ORIGINS to a JSON list, e.g. CORS_ORIGINS='["http://localhost:4173"]'
  cors_origins : list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

settings = Settings()

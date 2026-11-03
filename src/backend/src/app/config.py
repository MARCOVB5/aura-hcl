from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# src/backend/.env, should contain the env-vars in the sample .env.example
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"

class Settings(BaseSettings):
  model_config = SettingsConfigDict(env_file = ENV_FILE)

  jwt_secret: str = Field(min_length=32)

  database_url : str
  # origins allowed to call the API from a browser (the Vite dev server by default).
  # to override, set CORS_ORIGINS to a JSON list, e.g. CORS_ORIGINS='["http://localhost:4173"]'
  cors_origins : list[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "https://aura.piechu.id.vn"]

settings = Settings() # pyright : ignore[reportCallIssue]
# it errors out because the BaseSettings will search for the db's url in the .env but the lsp forces you to give an argument for it, just ignore it;

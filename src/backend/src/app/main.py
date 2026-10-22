from contextlib import asynccontextmanager
from app.api.routes import patients
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.db import engine, SessionLocal
from app.db.seed import seed_reference_data
from app.errors import AppError
from app.models import Base

@asynccontextmanager
async def lifespan(app : FastAPI):
  # temporary until the Alembic migrations are set up:
  # creates the missing tables, but never alters a table that already exists
  Base.metadata.create_all(engine)
  with SessionLocal() as session:
    seed_reference_data(session)
  yield

app = FastAPI(title="SI Alpha", lifespan=lifespan)

app.include_router(patients.router)

@app.exception_handler(AppError)
async def handle_app_error(request : Request, exc : AppError):
  return JSONResponse({"detail": exc.message}, status_code =exc.status)

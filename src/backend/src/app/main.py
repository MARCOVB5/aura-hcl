from app.api.routes import care, hospitalizations, patients
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.errors import AppError

app = FastAPI(title="SI Alpha")

# the frontend runs on another port, so the browser needs CORS headers to call the API
app.add_middleware(
  CORSMiddleware,
  allow_origins=settings.cors_origins,
  allow_methods=["*"],
  allow_headers=["*"],
)

app.include_router(patients.router)
app.include_router(hospitalizations.router)
app.include_router(care.router)

@app.exception_handler(AppError)
async def handle_app_error(request : Request, exc : AppError):
  return JSONResponse({"detail": exc.message}, status_code =exc.status)

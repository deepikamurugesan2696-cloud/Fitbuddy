from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import BASE_DIR, get_settings
from .database import init_db
from .routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


settings = get_settings()
app = FastAPI(
    title="FitBuddy – AI Fitness Plan Generator",
    description="AI-assisted 7-day fitness planning with Gemini, FastAPI, Jinja2 and SQLite.",
    version="1.0.0",
    lifespan=lifespan,
)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}

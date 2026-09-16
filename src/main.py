from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.app.config import settings
from src.app.database import create_db_and_tables
from src.app.routers import auth, predictions, refunds, reviews, users
from src.app.seed import seed_admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle for the application."""
    # Startup: create tables and seed the admin user
    create_db_and_tables()
    seed_admin()
    yield
    # Shutdown: nothing to clean up for now


app = FastAPI(
    title=settings.APP_NAME,
    description="API para o projeto com autenticação JWT, banco PostgreSQL e validação Pydantic.",
    version="1.0.0",
    lifespan=lifespan,
)


# ── Routers ───────────────────────────────────────────────

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(reviews.router)
app.include_router(predictions.router)
app.include_router(refunds.router)


# ── Health Check ──────────────────────────────────────────

@app.get("/health", tags=["Health Check"])
def health_check():
    return {
        "status": "ok",
        "message": "API operacional",
    }
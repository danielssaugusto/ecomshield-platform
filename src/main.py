from contextlib import asynccontextmanager

<<<<<<< HEAD
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
=======
from fastapi import FastAPI
>>>>>>> b6eb3ce935a1d7d0e6a23984cb49ca4a7766ae87

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


<<<<<<< HEAD
# ── Middleware: HTTP Security Headers ─────────────────────

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none';"
    return response


# ── Middleware: CORS Allowlist ─────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)


=======
>>>>>>> b6eb3ce935a1d7d0e6a23984cb49ca4a7766ae87
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
import base64
import hashlib
import re
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.staticfiles import StaticFiles

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
    docs_url=None,
    redoc_url=None,
)

STATIC_DIR = Path(__file__).resolve().parent / "app" / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/docs", include_in_schema=False)
def swagger_docs():
    response = get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger-ui.css",
        swagger_favicon_url="/static/favicon.svg",
    )
    inline_script = re.search(rb"<script>(.*?)</script>", response.body, re.DOTALL)
    if inline_script is None:
        raise RuntimeError("Não foi possível calcular o hash CSP do Swagger UI")
    digest = base64.b64encode(hashlib.sha256(inline_script.group(1)).digest()).decode()
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        f"script-src 'self' 'sha256-{digest}'; "
        "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
        "font-src 'self' data:; connect-src 'self'; "
        "object-src 'none'; base-uri 'self'; form-action 'self'; "
        "frame-ancestors 'none';"
    )
    return response


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
def swagger_redirect():
    return get_swagger_ui_oauth2_redirect_html()


@app.get("/redoc", include_in_schema=False)
def redoc_docs():
    response = get_redoc_html(
        openapi_url=app.openapi_url,
        title=f"{app.title} - ReDoc",
        redoc_js_url="/static/redoc.standalone.js",
        redoc_favicon_url="/static/favicon.svg",
        with_google_fonts=False,
    )
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
        "font-src 'self' data:; connect-src 'self'; "
        "object-src 'none'; base-uri 'self'; form-action 'self'; "
        "frame-ancestors 'none';"
    )
    return response


# ── Middleware: HTTP Security Headers ─────────────────────

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers.setdefault(
        "Content-Security-Policy",
        "default-src 'self'; object-src 'none'; base-uri 'self'; "
        "form-action 'self'; frame-ancestors 'none';",
    )
    return response


# ── Middleware: CORS Allowlist ─────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
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

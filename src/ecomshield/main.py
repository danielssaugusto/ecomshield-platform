from contextlib import asynccontextmanager

from fastapi import FastAPI

from ecomshield.db.database import create_tables
from ecomshield.routers import auth, classify


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_tables()
    yield

app = FastAPI(
    title="E-ComShield API",
    version="0.2.0",
    description="API de gestão de pedidos e reembolsos com autorização por recurso.",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(classify.router)


@app.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    return {"status": "ok"}

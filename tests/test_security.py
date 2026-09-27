import base64
import hashlib
import re

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from src.app.auth import create_access_token, get_password_hash
from src.app.database import get_session
from src.app.models import Prediction, RefundRequest, Review, User, UserRole
from src.app.rate_limiter import auth_rate_limiter
from src.main import app


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    auth_rate_limiter.reset()
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
    auth_rate_limiter.reset()


def create_test_user(session: Session, username: str, email: str, role: UserRole = UserRole.viewer) -> User:
    user = User(
        username=username,
        email=email,
        hashed_password=get_password_hash("password123"),
        role=role,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get_auth_header(username: str) -> dict[str, str]:
    token = create_access_token(data={"sub": username})
    return {"Authorization": f"Bearer {token}"}


# ── (a) Tentativa de acesso sem token ──────────────────────────────────────────

def test_unauthorized_access_without_token(client: TestClient):
    response = client.get("/users/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

    response_refunds = client.get("/refunds/")
    assert response_refunds.status_code == 401


# ── (b) Tentativa de acesso a recurso de outro usuário (BOLA) ─────────

def test_bola_access_other_user_resource_forbidden(client: TestClient, session: Session):
    user_a = create_test_user(session, "usera", "usera@example.com")
    user_b = create_test_user(session, "userb", "userb@example.com")

    # User B's refund request
    refund_b = RefundRequest(
        user_id=user_b.id,
        order_id="ORD-1002",
        reason="Defeito",
        amount=150.0,
    )
    session.add(refund_b)
    session.commit()
    session.refresh(refund_b)

    # User A attempts to access User B's profile
    headers_a = get_auth_header(user_a.username)
    resp_user = client.get(f"/users/{user_b.id}", headers=headers_a)
    assert resp_user.status_code == 403
    assert "Sem permissão" in resp_user.json()["detail"]

    # User A attempts to access User B's refund request
    resp_refund = client.get(f"/refunds/{refund_b.id}", headers=headers_a)
    assert resp_refund.status_code == 403
    assert "Sem permissão" in resp_refund.json()["detail"]


def test_review_and_prediction_are_private(client: TestClient, session: Session):
    user_a = create_test_user(session, "privatea", "privatea@example.com")
    user_b = create_test_user(session, "privateb", "privateb@example.com")
    review_b = Review(
        user_id=user_b.id,
        product_name="Produto",
        review_text="Texto de teste",
        overall_rating=3,
    )
    prediction_b = Prediction(
        user_id=user_b.id,
        input_data="{}",
        result="placeholder",
    )
    session.add(review_b)
    session.add(prediction_b)
    session.commit()
    session.refresh(review_b)
    session.refresh(prediction_b)

    headers_a = get_auth_header(user_a.username)
    assert client.get(f"/reviews/{review_b.id}", headers=headers_a).status_code == 403
    assert client.get(f"/predictions/{prediction_b.id}", headers=headers_a).status_code == 403
    assert client.get("/reviews/", headers=headers_a).json() == []
    assert client.get("/predictions/", headers=headers_a).json() == []


def test_public_registration_creates_viewer(client: TestClient):
    payload = {
        "username": "ordinary",
        "email": "ordinary@example.com",
        "password": "strongpassword123",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201
    assert response.json()["role"] == "viewer"


# ── (c) Envio de campo extra no body da request (Pydantic extra='forbid') ──────

def test_extra_fields_in_request_body_rejected(client: TestClient):
    payload = {
        "username": "newuser",
        "email": "newuser@example.com",
        "password": "strongpassword123",
        "extra_unauthorized_field": "hacked_value",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any(err.get("type") == "extra_forbidden" for err in errors)


def test_registration_cannot_assign_admin_role(client: TestClient, session: Session):
    payload = {
        "username": "attacker",
        "email": "attacker@example.com",
        "password": "strongpassword123",
        "role": "admin",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 422
    assert session.exec(select(User).where(User.username == "attacker")).first() is None


def test_disabled_user_cannot_login_or_reuse_token(client: TestClient, session: Session):
    user = create_test_user(session, "disabled", "disabled@example.com")
    token = get_auth_header(user.username)
    user.disabled = True
    session.add(user)
    session.commit()

    login = client.post(
        "/auth/token",
        data={"username": user.username, "password": "password123"},
    )
    assert login.status_code == 401
    assert client.get("/users/me", headers=token).status_code == 401


# ── Additional Security Verification Tests ────────────────────────────────────

def test_rate_limiting_on_auth_token_endpoint(client: TestClient, session: Session):
    create_test_user(session, "rateuser", "rateuser@example.com")
    form_data = {"username": "rateuser", "password": "wrongpassword"}

    # Exceed limit of 5 requests
    for _ in range(5):
        client.post("/auth/token", data=form_data)

    # 6th attempt should be blocked by Rate Limiter (429)
    response = client.post("/auth/token", data=form_data)
    assert response.status_code == 429
    assert "Retry-After" in response.headers
    assert "excedido" in response.json()["detail"]


def test_security_headers_and_cors_middleware(client: TestClient):
    response = client.get("/health", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    assert response.headers["Strict-Transport-Security"] == "max-age=31536000; includeSubDomains"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"
    assert "form-action 'self'" in response.headers["Content-Security-Policy"]
    assert "frame-ancestors 'none'" in response.headers["Content-Security-Policy"]
    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:3000"


def test_docs_use_local_assets_and_specific_csp(client: TestClient):
    response = client.get("/docs")
    assert response.status_code == 200
    assert "/static/swagger-ui-bundle.js" in response.text
    assert "/static/swagger-ui.css" in response.text
    assert "cdn.jsdelivr.net" not in response.text
    assert "sha256-" in response.headers["Content-Security-Policy"]
    inline_script = re.search(rb"<script>(.*?)</script>", response.content, re.DOTALL)
    assert inline_script is not None
    digest = base64.b64encode(hashlib.sha256(inline_script.group(1)).digest()).decode()
    assert f"'sha256-{digest}'" in response.headers["Content-Security-Policy"]
    assert client.get("/static/swagger-ui-bundle.js").status_code == 200
    assert client.get("/static/swagger-ui.css").status_code == 200

    redoc = client.get("/redoc")
    assert redoc.status_code == 200
    assert "/static/redoc.standalone.js" in redoc.text
    assert "cdn." not in redoc.text
    assert client.get("/static/redoc.standalone.js").status_code == 200

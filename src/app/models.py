"""
Domain models (SQLModel tables) and API schemas for the EcomShield platform.

Tables (table=True):  User, Review, Prediction, RefundRequest
Schemas (plain):      Token, TokenData, UserCreate, UserRead,
                      ReviewCreate, ReviewRead,
                      PredictionRead,
                      RefundRequestCreate, RefundRequestRead, RefundRequestUpdate
"""


from datetime import UTC, datetime
from enum import Enum

from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel

# ──────────────────────────────────────────────────────────
#  Enums
# ──────────────────────────────────────────────────────────

class UserRole(str, Enum):
    admin = "admin"
    analyst = "analyst"
    viewer = "viewer"


class RefundStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    denied = "denied"


# ──────────────────────────────────────────────────────────
#  SQLModel Tables
# ──────────────────────────────────────────────────────────

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, max_length=50)
    email: str = Field(unique=True, max_length=255)
    hashed_password: str
    role: UserRole = Field(default=UserRole.viewer)
    disabled: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )

    # Relationships
    reviews: list["Review"] = Relationship(back_populates="user")
    predictions: list["Prediction"] = Relationship(back_populates="user")
    refund_requests: list["RefundRequest"] = Relationship(back_populates="user")


class Review(SQLModel, table=True):
    __tablename__ = "reviews"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    product_name: str = Field(max_length=255)
    review_title: str | None = Field(default=None, max_length=255)
    review_text: str
    overall_rating: int = Field(ge=1, le=5)
    intent: str | None = Field(default=None, max_length=100)
    sentiment: str | None = Field(default=None, max_length=50)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )

    # Relationships
    user: User | None = Relationship(back_populates="reviews")


class Prediction(SQLModel, table=True):
    __tablename__ = "predictions"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    input_data: str
    result: str
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    model_version: str | None = Field(default=None, max_length=50)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )

    # Relationships
    user: User | None = Relationship(back_populates="predictions")


class RefundRequest(SQLModel, table=True):
    __tablename__ = "refund_requests"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    order_id: str = Field(max_length=100, index=True)
    reason: str
    amount: float = Field(ge=0.0)
    status: RefundStatus = Field(default=RefundStatus.pending)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
    )

    # Relationships
    user: User | None = Relationship(back_populates="refund_requests")


# ──────────────────────────────────────────────────────────
#  API Schemas (no table=True → pure Pydantic)
# ──────────────────────────────────────────────────────────

# ── Auth ──────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


# ── User ──────────────────────────────────────────────────

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: UserRole = UserRole.viewer


class UserRead(BaseModel):
    id: int
    username: str
    email: str
    role: UserRole
    disabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Review ────────────────────────────────────────────────

class ReviewCreate(BaseModel):
    product_name: str
    review_title: str | None = None
    review_text: str
    overall_rating: int = Field(ge=1, le=5)
    intent: str | None = None
    sentiment: str | None = None


class ReviewRead(BaseModel):
    id: int
    user_id: int
    product_name: str
    review_title: str | None
    review_text: str
    overall_rating: int
    intent: str | None
    sentiment: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Prediction ────────────────────────────────────────────

class PredictionRead(BaseModel):
    id: int
    user_id: int
    input_data: str
    result: str
    confidence: float | None
    model_version: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ── RefundRequest ─────────────────────────────────────────

class RefundRequestCreate(BaseModel):
    order_id: str
    reason: str
    amount: float = Field(ge=0.0)


class RefundRequestRead(BaseModel):
    id: int
    user_id: int
    order_id: str
    reason: str
    amount: float
    status: RefundStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RefundRequestUpdate(BaseModel):
    status: RefundStatus | None = None
    reason: str | None = None
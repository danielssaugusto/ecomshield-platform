from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


class UserRead(BaseModel):
    id: int
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ClassifyRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2_000)


class ClassifyResponse(BaseModel):
    intent: str
    probability: float = Field(ge=0, le=1)


class OrderCreate(BaseModel):
    reference: str = Field(min_length=3, max_length=64)
    description: str = Field(min_length=1, max_length=2_000)


class OrderRead(OrderCreate):
    id: int
    status: str

    model_config = ConfigDict(from_attributes=True)


class RefundCreate(BaseModel):
    reason: str = Field(min_length=3, max_length=2_000)


class RefundRead(RefundCreate):
    id: int
    order_id: int
    status: str

    model_config = ConfigDict(from_attributes=True)

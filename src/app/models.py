from pydantic import BaseModel, EmailStr
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

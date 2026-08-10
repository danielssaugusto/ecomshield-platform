from datetime import timedelta
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from src.app.config import settings
from src.app.models import Token, User
from src.app.auth import (
    verify_password,
    create_access_token,
    get_current_user,
    fake_users_db
)

app = FastAPI(
    title=settings.APP_NAME,
    description="API para o projeto com autenticação JWT e validação Pydantic.",
    version="1.0.0"
)

@app.get("/health", tags=["Health Check"])
def health_check():
    return {"status": "ok", "message": "API operacional"}

@app.post("/auth/login", response_model=Token, tags=["Autenticação"])
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user_dict = fake_users_db.get(form_data.username)
    if not user_dict or not verify_password(form_data.password, user_dict["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_dict["username"]}, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/protected", response_model=User, tags=["Rota Protegida"])
def read_protected_route(current_user: User = Depends(get_current_user)):
    return current_user
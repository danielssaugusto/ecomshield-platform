from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from src.app.auth import get_current_user
from src.app.database import get_session
<<<<<<< HEAD
from src.app.models import User, UserRead, UserRole
=======
from src.app.models import User, UserRead
>>>>>>> b6eb3ce935a1d7d0e6a23984cb49ca4a7766ae87

router = APIRouter(prefix="/users", tags=["Usuários"])


@router.get("/me", response_model=UserRead)
def read_current_user(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.get("/", response_model=list[UserRead])
def list_users(
    skip: int = 0,
    limit: int = 20,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
<<<<<<< HEAD
    if current_user.role == UserRole.admin:
        users = session.exec(
            select(User).offset(skip).limit(limit)
        ).all()
    else:
        users = [current_user]
=======
    users = session.exec(
        select(User).offset(skip).limit(limit)
    ).all()
>>>>>>> b6eb3ce935a1d7d0e6a23984cb49ca4a7766ae87
    return users


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
<<<<<<< HEAD
    if current_user.role != UserRole.admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para acessar os dados deste usuário",
        )

=======
>>>>>>> b6eb3ce935a1d7d0e6a23984cb49ca4a7766ae87
    user = session.get(User, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )

    return user

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from src.app.auth import get_current_user
from src.app.database import get_session
from src.app.models import Review, ReviewCreate, ReviewRead, User

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("/", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
def create_review(
    review_data: ReviewCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    review = Review(
        user_id=current_user.id,
        **review_data.model_dump(),
    )

    session.add(review)
    session.commit()
    session.refresh(review)

    return review


@router.get("/", response_model=list[ReviewRead])
def list_reviews(
    skip: int = 0,
    limit: int = 20,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    reviews = session.exec(
        select(Review).offset(skip).limit(limit)
    ).all()
    return reviews


@router.get("/{review_id}", response_model=ReviewRead)
def get_review(
    review_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    review = session.get(Review, review_id)

    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review não encontrada",
        )

    return review

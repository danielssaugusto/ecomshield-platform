from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from src.app.auth import get_current_user
from src.app.database import get_session
from src.app.models import Prediction, PredictionRead, User, UserRole

router = APIRouter(prefix="/predictions", tags=["Predição"])


@router.post("/predict", response_model=PredictionRead, status_code=201)
def predict(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Run prediction and persist the result.

    Currently returns a placeholder; the real ML model will be plugged in later.
    """
    prediction = Prediction(
        user_id=current_user.id,
        input_data="{}",
        result="Previsão realizada com sucesso (placeholder)",
        confidence=None,
        model_version="placeholder-v0",
    )

    session.add(prediction)
    session.commit()
    session.refresh(prediction)

    return prediction


@router.get("/", response_model=list[PredictionRead])
def list_predictions(
    skip: int = 0,
    limit: int = 20,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.admin:
        query = select(Prediction)
    else:
        query = select(Prediction).where(Prediction.user_id == current_user.id)

    predictions = session.exec(
        query.offset(skip).limit(limit)
    ).all()
    return predictions


@router.get("/{prediction_id}", response_model=PredictionRead)
def get_prediction(
    prediction_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    prediction = session.get(Prediction, prediction_id)

    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Predição não encontrada",
        )

    if current_user.role != UserRole.admin and prediction.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para acessar esta predição",
        )

    return prediction

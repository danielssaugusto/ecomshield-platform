from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from src.app.auth import get_current_user
from src.app.database import get_session
from src.app.models import Prediction, PredictionRead, User

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
    predictions = session.exec(
        select(Prediction)
        .where(Prediction.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    ).all()
    return predictions

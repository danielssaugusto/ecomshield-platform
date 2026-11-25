"""Authenticated intent classification endpoint."""
from functools import lru_cache
from pathlib import Path

import joblib
from fastapi import APIRouter, Depends, HTTPException, status

from ecomshield.db.models import User
from ecomshield.routers.auth import get_current_user
from ecomshield.schemas import ClassifyRequest, ClassifyResponse

router = APIRouter(tags=["intent classification"])
MODEL_PATH = Path(__file__).resolve().parents[3] / "models" / "bitext_intent_tfidf_logreg.joblib"


@lru_cache(maxsize=1)
def load_model():
    if not MODEL_PATH.exists():
        raise FileNotFoundError(f"Modelo não encontrado em {MODEL_PATH}")
    return joblib.load(MODEL_PATH)


@router.post("/classify", response_model=ClassifyResponse)
def classify(payload: ClassifyRequest, _: User = Depends(get_current_user)) -> ClassifyResponse:
    try:
        model = load_model()
        probabilities = model.predict_proba([payload.text])[0]
        index = int(probabilities.argmax())
        return ClassifyResponse(intent=str(model.classes_[index]), probability=float(probabilities[index]))
    except FileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Modelo de intenção indisponível") from exc

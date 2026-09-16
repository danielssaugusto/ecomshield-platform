from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from src.app.auth import get_current_user
from src.app.database import get_session
from src.app.models import (
    RefundRequest,
    RefundRequestCreate,
    RefundRequestRead,
    RefundRequestUpdate,
    User,
    UserRole,
)

router = APIRouter(prefix="/refunds", tags=["Reembolsos"])


@router.post("/", response_model=RefundRequestRead, status_code=status.HTTP_201_CREATED)
def create_refund_request(
    refund_data: RefundRequestCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    refund = RefundRequest(
        user_id=current_user.id,
        **refund_data.model_dump(),
    )

    session.add(refund)
    session.commit()
    session.refresh(refund)

    return refund


@router.get("/", response_model=list[RefundRequestRead])
def list_refund_requests(
    skip: int = 0,
    limit: int = 20,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.admin:
        query = select(RefundRequest)
    else:
        query = select(RefundRequest).where(
            RefundRequest.user_id == current_user.id
        )

    refunds = session.exec(
        query.offset(skip).limit(limit)
    ).all()

    return refunds


@router.get("/{refund_id}", response_model=RefundRequestRead)
def get_refund_request(
    refund_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    refund = session.get(RefundRequest, refund_id)

    if not refund:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitação de reembolso não encontrada",
        )

    if current_user.role != UserRole.admin and refund.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Sem permissão para acessar este reembolso",
        )

    return refund


@router.patch("/{refund_id}", response_model=RefundRequestRead)
def update_refund_request(
    refund_id: int,
    update_data: RefundRequestUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Somente administradores podem atualizar reembolsos",
        )

    refund = session.get(RefundRequest, refund_id)

    if not refund:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Solicitação de reembolso não encontrada",
        )

    update_fields = update_data.model_dump(exclude_unset=True)

    for field, value in update_fields.items():
        setattr(refund, field, value)

    refund.updated_at = datetime.now(UTC)

    session.add(refund)
    session.commit()
    session.refresh(refund)

    return refund

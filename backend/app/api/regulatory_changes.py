from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.regulatory_change import RegulatoryChange
from app.schemas.regulatory_change import RegulatoryChangeResponse


router = APIRouter(
    prefix="/api/regulatory-changes",
    tags=["Regulatory Changes"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get(
    "",
    response_model=List[RegulatoryChangeResponse]
)
def get_regulatory_changes(
    db: Session = Depends(get_db)
):
    changes = (
        db.query(RegulatoryChange)
        .order_by(RegulatoryChange.regulatory_change_id)
        .all()
    )

    return changes


@router.get(
    "/{regulatory_change_id}",
    response_model=RegulatoryChangeResponse
)
def get_regulatory_change(
    regulatory_change_id: str,
    db: Session = Depends(get_db)
):
    change = (
        db.query(RegulatoryChange)
        .filter(
            RegulatoryChange.regulatory_change_id
            == regulatory_change_id
        )
        .first()
    )

    if not change:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Regulatory change not found"
        )

    return change
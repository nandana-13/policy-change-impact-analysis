from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.regulatory_change import RegulatoryChange
from app.services.impact_engine_service import (
    get_impact_engine_service,
)
from app.schemas.impact_engine import ImpactAnalysisResponse


router = APIRouter(
    prefix="/impact-engine",
    tags=["Impact Engine"],
)


def get_db():
    """
    Create a database session for the current request.
    """
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get(
    "/regulatory-changes/{regulatory_change_id}",
    response_model=ImpactAnalysisResponse,
)
def analyze_regulatory_change(
    regulatory_change_id: str,
    top_k: int = Query(
        default=10,
        ge=1,
        le=50,
    ),
    legal_top_k: int = Query(
        default=5,
        ge=1,
        le=20,
    ),
    policy_evidence_top_k: int = Query(
        default=3,
        ge=1,
        le=10,
    ),
    db: Session = Depends(get_db),
):
    """
    Analyze the impact of a regulatory change.

    Pipeline:

        Regulatory Change
              ↓
        Candidate Policies
              ↓
        Legal Evidence
              ↓
        Company Policy Evidence
              ↓
        Direct / Indirect / No Impact
              ↓
        Impact Type
              ↓
        Expected Action
              ↓
        Explainable Result
    """

    regulatory_change = (
        db.query(RegulatoryChange)
        .filter(
            RegulatoryChange.regulatory_change_id
            == regulatory_change_id
        )
        .first()
    )

    if regulatory_change is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Regulatory change "
                f"'{regulatory_change_id}' not found."
            ),
        )

    service = get_impact_engine_service()

    try:
        result = service.analyze_regulatory_change(
            db=db,
            regulatory_change=regulatory_change,
            top_k=top_k,
            legal_top_k=legal_top_k,
            policy_evidence_top_k=policy_evidence_top_k,
        )

        return result

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Impact analysis failed: {str(exc)}",
        ) from exc
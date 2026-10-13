from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db

from app.schemas.impact_analysis import (
    ImpactAnalysisResponse,
    RegulatoryCandidateResponse,
)

from app.services.impact_analysis_service import (
    get_impact_analysis_service,
)


router = APIRouter(
    prefix="/impact-analysis",
    tags=["Impact Analysis"],
)


# ================================================================
# PHASE 2F.1
# REGULATORY CHANGE → CANDIDATE POLICIES
# ================================================================

@router.get(
    "/regulatory-changes/{regulatory_change_id}/candidates",
    response_model=RegulatoryCandidateResponse,
)
def get_candidate_policies(
    regulatory_change_id: str,

    top_k: int = Query(
        default=10,
        ge=1,
        le=50,
    ),

    db: Session = Depends(
        get_db
    ),
):

    service = (
        get_impact_analysis_service()
    )

    return (
        service.analyze_regulatory_change(
            db=db,
            regulatory_change_id=(
                regulatory_change_id
            ),
            top_k=top_k,
        )
    )


# ================================================================
# PHASE 2F.2
# COMPLETE IMPACT ANALYSIS
# ================================================================

@router.get(
    "/regulatory-changes/{regulatory_change_id}",
    response_model=ImpactAnalysisResponse,
)
def get_impact_analysis(
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

    db: Session = Depends(
        get_db
    ),
):

    service = (
        get_impact_analysis_service()
    )

    return (
        service.analyze_impact(
            db=db,
            regulatory_change_id=(
                regulatory_change_id
            ),
            top_k=top_k,
            legal_top_k=legal_top_k,
        )
    )
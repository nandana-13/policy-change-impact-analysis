from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.change_engine import (
    ChangeComparisonResponse,
)
from app.services.change_engine_service import (
    get_change_engine_service,
)


router = APIRouter(
    prefix="/change-engine",
    tags=["Change Engine"],
)


@router.get(
    "/policies/{policy_id}/compare",
    response_model=ChangeComparisonResponse,
)
def compare_policy_versions(
    policy_id: str,
    old_version: int = Query(
        ...,
        ge=1,
        description="Previous policy version number",
    ),
    new_version: int = Query(
        ...,
        ge=1,
        description="New policy version number",
    ),
    db: Session = Depends(get_db),
):
    """
    Compare two uploaded versions of the same policy.

    Example:

        GET
        /api/change-engine/policies/POL-001/compare
        ?old_version=1
        &new_version=2
    """

    service = get_change_engine_service()

    try:
        result = service.compare_versions(
            db=db,
            policy_id=policy_id,
            old_version_number=old_version,
            new_version_number=new_version,
        )

        return result

    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except RuntimeError as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Change Engine failed while "
                f"comparing policy versions: {exc}"
            ),
        ) from exc
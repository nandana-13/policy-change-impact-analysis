from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.policy import Policy
from app.models.policy_version import PolicyVersion
from app.schemas.policy_version import (
    PolicyVersionCreate,
    PolicyVersionResponse,
)


router = APIRouter(
    prefix="/api/policies",
    tags=["Policy Versions"]
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ============================================================
# GET ALL VERSIONS OF A POLICY
# ============================================================

@router.get(
    "/{policy_id}/versions",
    response_model=List[PolicyVersionResponse]
)
def get_policy_versions(
    policy_id: str,
    db: Session = Depends(get_db)
):
    policy = (
        db.query(Policy)
        .filter(
            Policy.policy_id == policy_id
        )
        .first()
    )

    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )

    versions = (
        db.query(PolicyVersion)
        .filter(
            PolicyVersion.policy_id == policy_id
        )
        .order_by(
            PolicyVersion.version_number
        )
        .all()
    )

    return versions


# ============================================================
# GET SINGLE POLICY VERSION
# ============================================================

@router.get(
    "/{policy_id}/versions/{version_number}",
    response_model=PolicyVersionResponse
)
def get_policy_version(
    policy_id: str,
    version_number: int,
    db: Session = Depends(get_db)
):
    version = (
        db.query(PolicyVersion)
        .filter(
            PolicyVersion.policy_id == policy_id,
            PolicyVersion.version_number == version_number
        )
        .first()
    )

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy version not found"
        )

    return version


# ============================================================
# CREATE POLICY VERSION
# ============================================================

@router.post(
    "/{policy_id}/versions",
    response_model=PolicyVersionResponse,
    status_code=status.HTTP_201_CREATED
)
def create_policy_version(
    policy_id: str,
    version_data: PolicyVersionCreate,
    db: Session = Depends(get_db)
):
    policy = (
        db.query(Policy)
        .filter(
            Policy.policy_id == policy_id
        )
        .first()
    )

    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )

    expected_prefix = f"{policy_id}-V"

    if not version_data.policy_version_id.startswith(
        expected_prefix
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "policy_version_id must start with "
                f"'{expected_prefix}'"
            )
        )

    existing_id = (
        db.query(PolicyVersion)
        .filter(
            PolicyVersion.policy_version_id
            == version_data.policy_version_id
        )
        .first()
    )

    if existing_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Policy version ID already exists"
        )

    existing_version = (
        db.query(PolicyVersion)
        .filter(
            PolicyVersion.policy_id == policy_id,
            PolicyVersion.version_number
            == version_data.version_number
        )
        .first()
    )

    if existing_version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "This version number already exists "
                "for the policy"
            )
        )

    policy_version = PolicyVersion(
        policy_version_id=version_data.policy_version_id,
        policy_id=policy_id,
        version_number=version_data.version_number,
        effective_date=version_data.effective_date,
        change_description=version_data.change_description,
        status=version_data.status,
        synthetic=version_data.synthetic,
    )

    db.add(policy_version)
    db.commit()
    db.refresh(policy_version)

    return policy_version
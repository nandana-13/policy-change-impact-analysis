from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.policy import Policy
from app.schemas.policy import (
    PolicyCreate,
    PolicyResponse,
    PolicyUpdate,
)


router = APIRouter(
    prefix="/api/policies",
    tags=["Policies"]
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ============================================================
# GET ALL POLICIES
# ============================================================

@router.get(
    "",
    response_model=List[PolicyResponse]
)
def get_policies(
    db: Session = Depends(get_db)
):
    policies = (
        db.query(Policy)
        .order_by(Policy.policy_id)
        .all()
    )

    return policies


# ============================================================
# GET SINGLE POLICY
# ============================================================

@router.get(
    "/{policy_id}",
    response_model=PolicyResponse
)
def get_policy(
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

    return policy


# ============================================================
# CREATE POLICY
# ============================================================

@router.post(
    "",
    response_model=PolicyResponse,
    status_code=status.HTTP_201_CREATED
)
def create_policy(
    policy_data: PolicyCreate,
    db: Session = Depends(get_db)
):
    existing_policy = (
        db.query(Policy)
        .filter(
            Policy.policy_id
            == policy_data.policy_id
        )
        .first()
    )

    if existing_policy:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Policy ID already exists"
        )

    policy = Policy(
        policy_id=policy_data.policy_id,
        policy_name=policy_data.policy_name,
        category=policy_data.category,
        department=policy_data.department,
        description=policy_data.description,
        synthetic=policy_data.synthetic,
    )

    db.add(policy)
    db.commit()
    db.refresh(policy)

    return policy


# ============================================================
# UPDATE POLICY
# ============================================================

@router.put(
    "/{policy_id}",
    response_model=PolicyResponse
)
def update_policy(
    policy_id: str,
    policy_data: PolicyUpdate,
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

    update_data = policy_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(
            policy,
            field,
            value
        )

    db.commit()
    db.refresh(policy)

    return policy
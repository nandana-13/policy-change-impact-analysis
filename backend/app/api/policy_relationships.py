from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.policy import Policy
from app.models.policy_relationship import PolicyRelationship
from app.schemas.policy_relationship import (
    PolicyRelationshipCreate,
    PolicyRelationshipResponse,
)


router = APIRouter(
    prefix="/api/policies",
    tags=["Policy Dependencies"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get(
    "/{policy_id}/dependencies",
    response_model=List[PolicyRelationshipResponse]
)
def get_policy_dependencies(
    policy_id: str,
    db: Session = Depends(get_db)
):
    # Check source policy exists
    policy = (
        db.query(Policy)
        .filter(Policy.policy_id == policy_id)
        .first()
    )

    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found"
        )

    relationships = (
        db.query(PolicyRelationship)
        .filter(
            PolicyRelationship.source_policy_id == policy_id
        )
        .order_by(PolicyRelationship.relationship_id)
        .all()
    )

    return relationships


@router.post(
    "/{policy_id}/dependencies",
    response_model=PolicyRelationshipResponse,
    status_code=status.HTTP_201_CREATED
)
def create_policy_dependency(
    policy_id: str,
    relationship_data: PolicyRelationshipCreate,
    db: Session = Depends(get_db)
):
    # Check source policy exists
    source_policy = (
        db.query(Policy)
        .filter(Policy.policy_id == policy_id)
        .first()
    )

    if not source_policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source policy not found"
        )

    # Check target policy exists
    target_policy = (
        db.query(Policy)
        .filter(
            Policy.policy_id
            == relationship_data.target_policy_id
        )
        .first()
    )

    if not target_policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target policy not found"
        )

    # Prevent relationship ID duplication
    existing_id = (
        db.query(PolicyRelationship)
        .filter(
            PolicyRelationship.relationship_id
            == relationship_data.relationship_id
        )
        .first()
    )

    if existing_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Relationship ID already exists"
        )

    # Prevent duplicate relationship
    existing_relationship = (
        db.query(PolicyRelationship)
        .filter(
            PolicyRelationship.source_policy_id == policy_id,
            PolicyRelationship.target_policy_id
            == relationship_data.target_policy_id,
            PolicyRelationship.relationship_type
            == relationship_data.relationship_type,
        )
        .first()
    )

    if existing_relationship:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This policy relationship already exists"
        )

    relationship = PolicyRelationship(
        relationship_id=relationship_data.relationship_id,
        source_policy_id=policy_id,
        target_policy_id=relationship_data.target_policy_id,
        relationship_type=relationship_data.relationship_type,
        synthetic=relationship_data.synthetic,
    )

    db.add(relationship)
    db.commit()
    db.refresh(relationship)

    return relationship
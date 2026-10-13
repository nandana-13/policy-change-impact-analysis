from sqlalchemy import Boolean, Column, Integer, String

from app.database import Base


class PolicyRelationship(Base):
    __tablename__ = "policy_relationships"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    relationship_id = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    source_policy_id = Column(
        String(50),
        nullable=False,
        index=True
    )

    target_policy_id = Column(
        String(50),
        nullable=False,
        index=True
    )

    relationship_type = Column(
        String(50),
        nullable=False
    )

    synthetic = Column(
        Boolean,
        nullable=False,
        default=True
    )
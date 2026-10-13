from sqlalchemy import Boolean, Column, Integer, String

from app.database import Base


class ImpactGroundTruth(Base):
    __tablename__ = "impact_ground_truth"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    impact_id = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    regulatory_change_id = Column(
        String(50),
        nullable=False,
        index=True
    )

    regulatory_act = Column(
        String(255),
        nullable=False
    )

    change_topic = Column(
        String(255),
        nullable=False
    )

    affected_policy_id = Column(
        String(50),
        nullable=False,
        index=True
    )

    relationship_type = Column(
        String(50),
        nullable=False
    )

    impact_type = Column(
        String(100),
        nullable=False
    )

    expected_action = Column(
        String(100),
        nullable=False
    )

    impact_status = Column(
        String(100),
        nullable=False
    )

    evidence_policy_version = Column(
        String(50),
        nullable=False,
        index=True
    )

    ground_truth_source = Column(
        String(100),
        nullable=False
    )

    synthetic = Column(
        Boolean,
        nullable=False,
        default=True
    )
from sqlalchemy import Boolean, Column, Date, Integer, String, Text

from app.database import Base


class PolicyVersion(Base):
    __tablename__ = "policy_versions"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    policy_version_id = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )

    policy_id = Column(
        String(50),
        nullable=False,
        index=True
    )

    version_number = Column(
        Integer,
        nullable=False
    )

    effective_date = Column(
        Date,
        nullable=False
    )

    change_description = Column(
        Text,
        nullable=False
    )

    status = Column(
        String(30),
        nullable=False
    )

    synthetic = Column(
        Boolean,
        nullable=False,
        default=True
    )
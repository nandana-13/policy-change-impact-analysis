from sqlalchemy import Boolean, Column, Integer, String, Text

from app.database import Base


class RegulatoryChange(Base):
    __tablename__ = "regulatory_changes"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    regulatory_change_id = Column(
        String(50),
        unique=True,
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

    change_description = Column(
        Text,
        nullable=False
    )

    synthetic = Column(
        Boolean,
        nullable=False,
        default=True
    )
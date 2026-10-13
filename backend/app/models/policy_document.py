from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class PolicyDocument(Base):
    __tablename__ = "policy_documents"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    document_id = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    policy_id = Column(
        String(50),
        nullable=False,
        index=True
    )

    policy_version_id = Column(
        String(50),
        nullable=False,
        index=True
    )

    version_number = Column(
        Integer,
        nullable=False
    )

    file_name = Column(
        String(255),
        nullable=False
    )

    file_path = Column(
        String(500),
        nullable=False
    )

    content_type = Column(
        String(100),
        nullable=False
    )

    file_size = Column(
        Integer,
        nullable=False
    )

    synthetic = Column(
        Boolean,
        nullable=False,
        default=False
    )

    uploaded_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
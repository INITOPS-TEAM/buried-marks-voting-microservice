import uuid
from sqlalchemy import Column, Integer, DateTime, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.db.session import Base


class Poll(Base):
    __tablename__ = "polls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String, nullable=False)
    target_id = Column(Integer, nullable=False)
    created_by = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="active")
    total_eligible = Column(Integer, nullable=False)
    ends_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class Vote(Base):
    __tablename__ = "votes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    poll_id = Column(UUID(as_uuid=True), nullable=False)
    voter_id = Column(Integer, nullable=False)
    choice = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('poll_id', 'voter_id', name='unique_vote'),
    )

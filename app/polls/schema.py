from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PollBase(BaseModel):
    type: str = Field(..., example="ban", description="Type: ban, level_up, level_top")
    target_id: int = Field(..., example="123")


class PollCreate(PollBase):
    pass


class PollRead(PollBase):
    id: UUID
    status: str
    created_by: int
    total_eligible: int
    ends_at: datetime
    created_at: datetime
    model_config = {"from_attributes": True}


class VoteCreate(BaseModel):
    poll_id: UUID
    voter_id: int
    choice: str = Field(..., example="for", description="for or against")


class VoteRead(VoteCreate):
    id: UUID
    created_at: datetime
    model_config = {"from_attributes": True}


class PollResult(BaseModel):
    poll_id: UUID
    status: str
    votes_for: int
    votes_against: int
    total_voted: int
    total_eligible: Optional[int] = None
    success: bool
    model_config = {"from_attributes": True}

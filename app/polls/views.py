from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import verify_jwt
from app.core.db.session import get_db
from app.polls import schema as schemas
from app.polls.models import Poll, Vote
from app.polls.service import PollService

router = APIRouter()


@router.post("/", response_model=schemas.PollRead, status_code=201)
async def create_poll(
    payload: schemas.PollCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(verify_jwt),
):
    # check initiator rights
    if payload.type == "ban" and not user["inspector"]:
        raise HTTPException(status_code=403, detail="Only inspector can initiate ban")

    if payload.type == "level_up" and user["role"] != "1":
        raise HTTPException(status_code=403, detail="Only role 1 can request level up")

    if payload.type == "level_top" and user["role"] != "2":
        raise HTTPException(status_code=403, detail="Only role 2 can request level top")

    # the target should be the user himself
    if payload.type in ("level_up", "level_top"):
        if payload.target_id != user["user_id"]:
            raise HTTPException(
                status_code=403, detail="You can only nominate yourself"
            )

    # check if there is no active vote for this user
    existing = await db.execute(
        select(Poll).where(
            Poll.target_id == payload.target_id,
            Poll.type == payload.type,
            Poll.status == "active",
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409, detail="Active poll already exists for this user"
        )

    # get the number of eligible users
    total_eligible = await PollService.get_total_eligible(payload.type)

    poll = Poll(
        type=payload.type,
        target_id=payload.target_id,
        created_by=user["user_id"],
        status="active",
        total_eligible=total_eligible,
        ends_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )

    db.add(poll)
    await db.commit()
    await db.refresh(poll)

    logger.info(f"Poll {poll.id} created by {user['user_id']}")
    return poll


@router.post("/{poll_id}/vote", response_model=schemas.VoteRead, status_code=201)
async def cast_vote(
    poll_id: UUID,
    payload: schemas.VoteCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(verify_jwt),
):
    # check if the vote exists and is active
    result = await db.execute(select(Poll).where(Poll.id == poll_id))
    poll = result.scalar_one_or_none()

    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    if poll.status != "active":
        raise HTTPException(status_code=400, detail="Poll is not active")
    if datetime.now(timezone.utc) > poll.ends_at.replace(tzinfo=timezone.utc):
        raise HTTPException(status_code=400, detail="Poll has expired")

    # voter rights verification
    if poll.type == "ban":
        pass
    elif poll.type == "level_up" and user["role"] not in ("2", "3"):
        raise HTTPException(status_code=403, detail="Only role 2 or 3 can vote")
    elif poll.type == "level_top" and user["role"] != "3":
        raise HTTPException(status_code=403, detail="Only role 3 can vote")

    # checking if the user has already voted
    existing_vote = await db.execute(
        select(Vote).where(Vote.poll_id == poll_id, Vote.voter_id == user["user_id"])
    )
    if existing_vote.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Already voted")

    vote = Vote(poll_id=poll_id, voter_id=user["user_id"], choice=payload.choice)

    db.add(vote)
    await db.commit()
    await db.refresh(vote)

    logger.info(f"Vote cast by {user['user_id']} on poll {poll_id}")
    return vote


@router.get("/{poll_id}", response_model=schemas.PollRead)
async def get_poll(
    poll_id: UUID, db: AsyncSession = Depends(get_db), user: dict = Depends(verify_jwt)
):
    result = await db.execute(select(Poll).where(Poll.id == poll_id))
    poll = result.scalar_one_or_none()

    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")
    return poll


@router.get("/{poll_id}/result", response_model=schemas.PollResult)
async def get_poll_result(
    poll_id: UUID, db: AsyncSession = Depends(get_db), user: dict = Depends(verify_jwt)
):
    result = await db.execute(select(Poll).where(Poll.id == poll_id))
    poll = result.scalar_one_or_none()

    if not poll:
        raise HTTPException(status_code=404, detail="Poll not found")

    votes_for = await db.execute(
        select(func.count(Vote.id)).where(Vote.poll_id == poll_id, Vote.choice == "for")
    )
    votes_against = await db.execute(
        select(func.count(Vote.id)).where(
            Vote.poll_id == poll_id, Vote.choice == "against"
        )
    )

    vf = votes_for.scalar()
    va = votes_against.scalar()
    total_voted = vf + va

    return schemas.PollResult(
        poll_id=poll.id,
        status=poll.status,
        votes_for=vf,
        votes_against=va,
        total_voted=total_voted,
        total_eligible=poll.total_eligible if poll.type == "ban" else None,
        success=poll.status == "success",
    )

import os
from datetime import datetime, timezone

import httpx
from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.polls.models import Poll, Vote

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL")


class PollService:

    @staticmethod
    async def get_total_eligible(poll_type: str) -> int:
        """Get the number of eligible users from auth-service"""
        try:
            async with httpx.AsyncClient() as client:
                if poll_type == "ban":
                    resp = await client.get(f"{AUTH_SERVICE_URL}/api/users/count/")
                elif poll_type == "level_up":
                    resp = await client.get(
                        f"{AUTH_SERVICE_URL}/api/users/count/", params={"role": "2,3"}
                    )
                elif poll_type == "level_top":
                    resp = await client.get(
                        f"{AUTH_SERVICE_URL}/api/users/count/", params={"role": "3"}
                    )
                return resp.json().get("count", 10)
        except Exception as e:
            logger.warning(f"Auth service unavailable: {e}, using default")
            return 10  # fallback

    @staticmethod
    def check_success(poll: Poll, votes_for: int, votes_against: int) -> bool:
        """Check the success condition for each type"""
        total_voted = votes_for + votes_against

        if poll.type == "ban":
            return votes_for > poll.total_eligible / 2

        elif poll.type == "level_up":
            if total_voted == 0:
                return False
            return votes_for / total_voted > 0.5

        elif poll.type == "level_top":
            if total_voted == 0:
                return False
            return votes_for / total_voted >= 0.8

        return False

    @staticmethod
    async def trigger_auth_action(poll: Poll):
        """Perform an action in auth-service after a successful vote"""
        internal_token = os.environ.get("DJANGO_SECRET_KEY")
        headers = {"X-Internal-Token": internal_token}
        try:
            async with httpx.AsyncClient() as client:
                if poll.type == "ban":
                    resp = await client.post(
                        f"{AUTH_SERVICE_URL}/api/users/{poll.target_id}/ban/",
                        headers=headers,
                    )
                    resp.raise_for_status()
                elif poll.type == "level_up":
                    resp = await client.patch(
                        f"{AUTH_SERVICE_URL}/api/users/{poll.target_id}/role/",
                        json={"role": "2"},
                        headers=headers,
                    )
                    resp.raise_for_status()
                elif poll.type == "level_top":
                    resp = await client.patch(
                        f"{AUTH_SERVICE_URL}/api/users/{poll.target_id}/role/",
                        json={"role": "3"},
                        headers=headers,
                    )
                    resp.raise_for_status()

            logger.success(f"Auth action triggered for poll {poll.id}")
        except Exception as e:
            logger.error(f"Auth service error: {e}")
            raise

    @staticmethod
    async def close_expired_polls(db: AsyncSession):
        """Close all pending votes — scheduler is called"""
        result = await db.execute(
            select(Poll).where(
                Poll.status == "active", Poll.ends_at <= datetime.now(timezone.utc)
            )
        )
        expired_polls = result.scalars().all()

        for poll in expired_polls:
            # count the votes
            vf = await db.execute(
                select(func.count(Vote.id)).where(
                    Vote.poll_id == poll.id, Vote.choice == "for"
                )
            )
            va = await db.execute(
                select(func.count(Vote.id)).where(
                    Vote.poll_id == poll.id, Vote.choice == "against"
                )
            )
            votes_for = vf.scalar()
            votes_against = va.scalar()

            # check the success condition
            success = PollService.check_success(poll, votes_for, votes_against)

            if success:
                try:
                    await PollService.trigger_auth_action(poll)
                    poll.status = "success"
                except Exception:
                    poll.status = "pending_action"
            else:
                poll.status = "failed"

            await db.commit()
            logger.info(f"Poll {poll.id} closed with status {poll.status}")

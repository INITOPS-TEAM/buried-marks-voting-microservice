# app/scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from app.core.db.session import AsyncSessionLocal
from app.polls.service import PollService

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('interval', minutes=1)
async def close_expired_polls():
    logger.info("Scheduler: checking expired polls...")
    async with AsyncSessionLocal() as db:
        await PollService.close_expired_polls(db)
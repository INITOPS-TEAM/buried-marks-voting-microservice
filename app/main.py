from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.logger import init_logging
from app.core.main_router import router as main_router
from app.polls.views import router as polls_router
from app.scheduler import scheduler

load_dotenv(".env")

@asynccontextmanager
async def lifespan(app: FastAPI):
# startup
    scheduler.start()
    logger.info("Scheduler started")
    yield
# shutdown
    scheduler.shutdown()
    logger.info("Scheduler stopped")

app = FastAPI(title="Voting Service", lifespan=lifespan)

origins = ["http://localhost"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(main_router)
app.include_router(polls_router, prefix="/api/polls", tags=["polls"])

init_logging()
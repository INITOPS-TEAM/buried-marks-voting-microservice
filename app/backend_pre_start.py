import logging
import os

from sqlalchemy import create_engine, text
from tenacity import (after_log, before_log, retry, stop_after_attempt,
                      wait_fixed)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


raw_url = os.getenv("DATABASE_URL", "")
DATABASE_URL = raw_url.replace("+asyncpg", "+psycopg")

max_tries = 60 * 5
wait_seconds = 1


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
def init() -> None:
    try:

        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        raise e


def main() -> None:
    logger.info("Initializing service (waiting for DB)...")
    init()
    logger.info("DB is up! Service ready to start.")


if __name__ == "__main__":
    main()

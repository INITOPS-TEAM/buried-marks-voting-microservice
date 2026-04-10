import logging
import os
from urllib.parse import quote_plus

import boto3
from sqlalchemy import create_engine, text
from tenacity import after_log, before_log, retry, stop_after_attempt, wait_fixed

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_HOST = os.environ["DB_HOST"]
DB_USER = os.environ["POSTGRES_USER"]
DB_NAME = os.environ["POSTGRES_DB"]
DB_PORT = int(os.getenv("DB_PORT", "5432"))
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "eu-north-1")

max_tries = 60 * 5
wait_seconds = 1


def provide_token() -> str:
    client = boto3.client("rds", region_name=AWS_REGION)
    return client.generate_db_auth_token(
        DBHostname=DB_HOST,
        Port=DB_PORT,
        DBUsername=DB_USER,
        Region=AWS_REGION,
    )


def build_sync_url() -> str:
    token = quote_plus(provide_token())
    return (
        f"postgresql+psycopg://{DB_USER}:{token}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )


@retry(
    stop=stop_after_attempt(max_tries),
    wait=wait_fixed(wait_seconds),
    before=before_log(logger, logging.INFO),
    after=after_log(logger, logging.WARN),
)
def init() -> None:
    try:
        url = build_sync_url()
        engine = create_engine(
            url,
            connect_args={
                'sslmode': 'verify-ca',
                'sslrootcert':  '/app/global-bundle.pem',
            },
        )
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

import os
import ssl
import boto3

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from urllib.parse import quote_plus

load_dotenv(".env")

Base = declarative_base()

DB_HOST = os.environ["DB_HOST"]
DB_USER = os.environ["POSTGRES_USER"]
DB_NAME = os.environ["POSTGRES_DB"]
DB_PORT = int(os.getenv("DB_PORT", "5432"))
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "eu-north-1")


def provide_token() -> str:
    client = boto3.client("rds", region_name=AWS_REGION)
    token = client.generate_db_auth_token(
        DBHostname=DB_HOST,
        Port=DB_PORT,
        DBUsername=DB_USER,
        Region=AWS_REGION,
    )
    return token


def build_database_url() -> str:
    token = provide_token()
    encoded_token = quote_plus(token)
    return (
        f"postgresql+asyncpg://{DB_USER}:{encoded_token}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )


def engine_with_iam():

    url = build_database_url()

    ssl_ctx = ssl.create_default_context(cafile="/app/global-bundle.pem")
    ssl_ctx.verify_mode = ssl.CERT_REQUIRED

    return create_async_engine(
        url,
        connect_args={"ssl": ssl_ctx},
        pool_pre_ping=True,
        pool_recycle=600,
        pool_size=5,
        max_overflow=10,
    )


engine = engine_with_iam()

AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

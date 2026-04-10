import os
import ssl
import boto3

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import event, create_engine
from urllib.parse import quote_plus

load_dotenv(".env")

Base = declarative_base()

DB_HOST = os.environ["DB_HOST"]
DB_USER = os.environ["POSTGRES_USER"]
DB_NAME = os.environ["POSTGRES_DB"]
DB_PORT = int(os.getenv("DB_PORT", "5432"))
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "eu-north-1")

ssl_ctx = ssl.create_default_context(cafile="/app/global-bundle.pem")
ssl_ctx.verify_mode = ssl.CERT_REQUIRED
engine = create_async_engine(
    f"postgresql+asyncpg:///",
    connect_args={"ssl": ssl_ctx},
    pool_pre_ping=True,
    pool_recycle=600,
    pool_size=5,
    max_overflow=10,
)

@event.listens_for(engine.sync_engine, "do_connect")
def provide_token(dialect, conn_rec, cargs, cparams):
    client = boto3.client("rds")
    token = client.generate_db_auth_token(DBHostname=DB_HOST, Port=DB_PORT, DBUsername=DB_USER, Region=AWS_REGION)
    # set up db connection parameters, alternatively we can get these from boto3 describe_db_instances
    cparams['host'] = DB_HOST
    cparams['port'] = DB_PORT
    cparams['user'] = DB_USER
    cparams['password'] = token
    cparams['database'] = DB_NAME
    print(token)


AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

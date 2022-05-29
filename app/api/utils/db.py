from api.utils.logger import logger, myself
from config import Config, Network # api specific config
from sqlalchemy.pool import QueuePool
from sqlalchemy.sql import text
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

CFG = Config[Network]

engine = None

def get_engine():
    global engine
    if engine:
        return engine
    engine = create_async_engine(
        CFG.csErgopad,
        echo=True,
        poolclass=QueuePool,
        pool_pre_ping=True,
        future=True,
    )
    return engine

engine = get_engine()

async def init_db():
    async with engine.begin() as con:
        await con.run_sync(SQLModel.metadata.create_all)

# Use this with ORM
async def get_session() -> AsyncSession:
    with Session(engine) as session:
        async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as session:
            yield session

# Use with SQL statements
# text() prevents sql injection attacks
async def fetch(query: str, params: dict = {}):
    try:        
        async with engine.begin() as con:
            res = await con.execute(text(query), params)
            if res.returns_rows:
                return res.fetchall()
            else:
                return {'rows': 0}
    except Exception as e:
        logger.error(f'ERR:FETCH: {e}')


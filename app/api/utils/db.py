from api.utils.logger import logger, myself, LEIF
from config import Config, Network # api specific config

from sqlmodel import SQLModel, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.sql import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

CFG = Config[Network]
engine = None

# async connection to postgres
def get_engine():
    try:
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
    
    except Exception as e:
        logger.error(f'ERR:{myself()}: {e}')
        return None

engine = get_engine()

# automatically build the models
async def init_db():
    try:
        async with engine.begin() as con:
            await con.run_sync(SQLModel.metadata.create_all)

    except Exception as e:
        logger.error(f'ERR:{myself()}: {e}')

# use with ORM
async def get_session() -> AsyncSession:
    try:
        with Session(engine) as session:
            async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
            async with async_session() as session:
                yield session

    except Exception as e:
        logger.error(f'ERR:{myself()}: {e}')

# use with SQL statements (param binding)
async def fetch(query: str, params: dict = {}):
    try:
        async with engine.begin() as con:
            res = await con.execute(text(query), params)
            if res.returns_rows:
                return res.fetchall()
            else:
                return {'rows': 0}

    except Exception as e:
        logger.error(f'ERR:{myself()}: {e}')
        return {}

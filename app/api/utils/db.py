from api.utils.logger import logger, myself, LEIF
from config import Config, Network # api specific config

from sqlmodel import SQLModel, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy.sql import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

CFG = Config[Network]
engines = {}

# async connection to postgres
def get_engine(cs):
    try:
        global engines
        return create_async_engine(
            cs,
            echo=True,
            poolclass=QueuePool,
            pool_pre_ping=True, 
            future=True,
        )
    
    except Exception as e:
        logger.error(f'ERR:{myself()}: {e}')
        return None

engines['ergopad'] = get_engine(CFG.csErgopad)
engines['explorer'] = get_engine(CFG.csExplorer)

# automatically build the models
async def init_db():
    try:
        for cs in engines:
            logger.log(LEIF, f'engine {cs}: {type(engines[cs])}')
            engine = engines[cs]
            async with engine.begin() as con:
                await con.run_sync(SQLModel.metadata.create_all)

    except Exception as e:
        logger.error(f'ERR:{myself()}: {e}')

# use with ORM
async def get_session(cs) -> AsyncSession:
    try:
        with Session(engines[cs]) as session:
            async_session = sessionmaker(engines[cs], class_=AsyncSession, expire_on_commit=False)
            async with async_session() as session:
                yield session

    except Exception as e:
        logger.error(f'ERR:{myself()}: {e}')

# use with SQL statements (param binding)
async def fetch(query: str, params: dict = {}, eng: str = 'ergopad'):
    try:
        async with engines[eng].begin() as con:
            res = await con.execute(text(query), params)
            if res.returns_rows:
                rows = res.fetchall()
                return [dict(r) for r in rows]
            else:
                return [{'nope': 0}]

    except Exception as e:
        logger.error(f'ERR:{myself()}: {e}')
        return {}

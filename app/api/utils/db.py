import asyncpg

from logger import logger, myself
from config import Config, Network # api specific config
from sqlalchemy.pool import QueuePool
from sqlalchemy.sql import text
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.exc import OperationalError

CFG = Config[Network]

class Database:

    def __init__(self):
        self.dsn = CFG.connectionString
        self._cursor = None
        self._connection_pool = None
        self.con = None

    async def connect(self):
        if not self._connection_pool:
            try:
                self._connection_pool = await asyncpg.create_pool(
                    self.dsn,
                    min_size=1,
                    max_size=10,
                    command_timeout=60,
                    max_inactive_connection_lifetime=3,
                )
            except Exception as e:
                logger.error(f'ERR {myself()}: {e}')

    async def fetch(self, query: str):
        if not self._connection_pool:
            await self.connect()
        else:
            self.con = await self._connection_pool.acquire()
            try:
                res = await self.con.fetch(query)
                return res
            except Exception as e:
                logger.error(f'ERR {myself()}: {e}')
            finally:
                await self._connection_pool.release(self.con)

# alternate method using sync connection
engine = None

def get_engine():
    global engine
    if engine:
        return engine
    engine = create_engine(
        CFG.csErgopad,
        echo=True,
        poolclass=QueuePool,
        pool_pre_ping=True,
        # pool_size=15,
        # max_overflow=5,
        echo_pool="debug"
    )
    return engine

engine = get_engine()

def get_session():
    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except Exception as exc:
            session.rollback()
            raise exc
        finally:
            session.close()

def init_db_sqlalchemy():
    SQLModel.metadata.create_all(engine)

def execute(db: Session, query, *args, **kwargs):
    try:
        stmt = text(query)
        result = db.execute(stmt, *args, **kwargs)
        db.commit()
        return result
    except (Exception, OperationalError) as e:
        logger.error(f'ERR {myself()}: {e}')
    finally:
        db.close()
from sqlalchemy import create_engine
from config import Config, Network # api specific config

CFG = Config[Network]

engDanaides = create_engine(CFG.csDanaides)

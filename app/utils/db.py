from sqlalchemy import create_engine
from config import Config, Network # api specific config

CFG = Config[Network]

dbErgopad = create_engine(CFG.connectionString)

# https://fastapi.tiangolo.com/advanced/async-sql-databases/
# ...if using async
# from databases import Database
# dbErgopad = Database(CFG.connectionString)
# dbExplorer = databases.Database(CFG.csExplorer)

from databases import Database

from config import Config, Network # api specific config

CFG = Config[Network]

# https://fastapi.tiangolo.com/advanced/async-sql-databases/
dbErgopad = Database(CFG.connectionString)
# dbExplorer = databases.Database(CFG.csExplorer)

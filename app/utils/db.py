import databases

from config import Config, Network # api specific config

CFG = Config[Network]

# https://fastapi.tiangolo.com/advanced/async-sql-databases/
dbErgopad = databases.Database(CFG.csErgopad)
dbExplorer = databases.Database(CFG.csExplorer)

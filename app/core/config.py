from config import Config, Network  # api specific config
CFG = Config[Network]

PROJECT_NAME = "ERGOPAD"
SQLALCHEMY_DATABASE_URI = CFG.connectionString
API_V1_STR = "/api"

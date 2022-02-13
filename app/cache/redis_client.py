import redis
from config import Config, Network

CFG = Config[Network]

redisClient = redis.Redis(
    host=CFG.redisHost,
    port=CFG.redisPort,
)


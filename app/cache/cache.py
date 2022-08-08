import json

from cache.redis_client import redisClient
from decimal import *

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return json.JSONEncoder.default(self, obj)

class RedisCache:
    def __init__(self, timeout: int = 900):
        self.client = redisClient
        # default 15 mins
        self.timeout = timeout

    def get(self, key: str):
        val = self.client.get(key)
        if val:
            return json.loads(val)

    def set(self, key: str, value, timeout: int = -1):
        if timeout == -1:
            timeout = self.timeout
        value = json.dumps(value, cls=DecimalEncoder)
        self.client.setex(key, timeout, value)

    def invalidate(self, key):
        return self.client.delete(key)


cache = RedisCache()
# cached = cache.get(key)
# if cached != None:
#   return cached

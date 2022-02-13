from cache.redis_client import redisClient

import json


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
        value = json.dumps(value)
        self.client.setex(key, timeout, value)


cache = RedisCache()
# cached = cache.get(key)
# if cached != None:
#   return cached

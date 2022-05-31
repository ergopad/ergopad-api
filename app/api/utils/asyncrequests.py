from aiohttp import TCPConnector, ClientSession, ClientTimeout
from api.utils.logger import logger, myself, LEIF

class Res:
    def __init__(self, ok=False, content=''):
        self.ok = ok
        self.content = content
    
    def json(self):
        return self.content

class Req:
    def __init__(self):
        logger.debug('async request init')

    def __await__(self):
        async def closure():
            return self()        
        return closure().__await__()

    async def __aenter__(self):
        self.conn = TCPConnector(limit=None, ttl_dns_cache=300)
        self.timeout = ClientTimeout(connect=1)
        self.session = ClientSession(connector=self.conn, timeout=self.timeout)
        return self

    async def __aexit__(self, *args, **kwargs):
        await self.session.close()
        await self.conn.close()

    async def get(self, url, headers=None):
        try:
            async with self.session.get(url, headers=headers, ssl=False) as ses:
                if ses.ok:
                    try: 
                        return Res(True, await ses.json())

                    except:
                        logger.warning('async request non-json response')
                        return Res(False, {})
                else:
                    logger.warning('async request response not ok')
                    return Res(False, {})

        except Exception as e:
            logger.warning('ERR: async request')
            return Res(False, {})

# async def main():
#     url = 'http://52.12.102.149:9090/api/v1/info'
#     async with Req() as r:
#         print(await r.get(url))
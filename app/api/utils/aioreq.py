import json 

from aiohttp import TCPConnector, ClientSession, ClientTimeout
from api.utils.logger import logger, myself, LEIF

class Res:
    def __init__(self, ok=False, content='', text=''):
        self.ok = ok
        self.content = content
        self.text = text
        # self.json = json

    def json(self):
        d = json.JSONDecoder() 
        if type(self.content) is bytes:
            content = self.content.decode('utf-8')
        else:
            content = str(self.content)

        # if this is already in json format, return
        try: return json.loads(content)
        except: pass

        # likely a list of dicts, and need to parse in chunks
        j = []
        idx = 0
        while True:
            try: 
                res, idx = d.raw_decode(content, idx)
                j.append(json.loads(res))
            except: 
                break    
        return j

class Req:
    def __init__(self):
        # logger.debug('async request init')
        True

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

    # requests.get
    async def get(self, url, headers=None):
        try:
            # sanity check
            if headers is not None:
                if type(headers) is not dict:
                    logger.warning('headers not in dict format')

            async with self.session.get(url, headers=headers, ssl=False) as ses:
                if ses.ok:
                    empty_bytes = b''
                    content = empty_bytes
                    while True:
                        chunk = await ses.content.read(8)
                        if chunk == empty_bytes:
                            break
                        content += chunk

                    text = str(ses.text)
                    return Res(ok=True, content=content, text=text)

                else:
                    logger.warning('async request response not ok')
                    return Res(False, {})

        except Exception as e:
            logger.error(f'ERR: async request {e}')
            return Res(False, {})

    # requests.post
    async def post(self, url, data=None, headers=None):
        try:
            # sanity check
            if headers is not None:
                if type(headers) is not dict:
                    logger.warning('headers not in dict format')

            async with self.session.post(url, headers=headers, data=data, ssl=False) as ses:
                if ses.ok:
                    try: 
                        return Res(True, await ses.json())

                    except:
                        logger.warning('async request non-json response')
                        return Res(False, {})
                else:
                    logger.warning('async request response not ok')
                    logger.debug(ses.text)
                    return Res(False, {})

        except Exception as e:
            logger.error(f'ERR: async request {e}')
            return Res(False, {})

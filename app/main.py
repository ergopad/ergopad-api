import uvicorn
import time, os

from fastapi.encoders import jsonable_encoder
from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware

from api.utils.logger import logger, myself, LEIF
from api.utils.db import init_db, fetch

from api.v1.routes.users         import users_router
from api.v1.routes.auth          import auth_router
from api.v1.routes.asset         import asset_router
from api.v1.routes.blockchain    import blockchain_router
from api.v1.routes.util          import util_router
from api.v1.routes.projects      import projects_router
from api.v1.routes.vesting       import vesting_router
from api.v1.routes.whitelist     import whitelist_router
from api.v1.routes.contribution  import contribution_router
from api.v1.routes.events        import events_router
from api.v1.routes.purchase      import purchase_router
from api.v1.routes.jobs          import jobs_router
from api.v1.routes.staking       import staking_router
from api.v1.routes.announcements import announcement_router
from api.v1.routes.tutorials     import tutorial_router
from api.v1.routes.faq           import faq_router
from api.v1.routes.notifications import notification_router

from core import config
from core.auth import get_current_active_user

AUDIT_REQUESTS = True
DEBUG = True

app = FastAPI(
    title=config.PROJECT_NAME,
    docs_url="/api/docs",
    openapi_url="/api"
)

#region Routers
app.include_router(users_router,        prefix="/api/users",         tags=["users"], dependencies=[Depends(get_current_active_user)])
app.include_router(auth_router,         prefix="/api/auth",          tags=["auth"])
app.include_router(asset_router,        prefix="/api/asset",         tags=["asset"])
app.include_router(blockchain_router,   prefix="/api/blockchain",    tags=["blockchain"])
app.include_router(projects_router,     prefix="/api/projects",      tags=["projects"])
app.include_router(util_router,         prefix="/api/util",          tags=["util"])
app.include_router(vesting_router,      prefix="/api/vesting",       tags=["vesting"])
app.include_router(whitelist_router,    prefix="/api/whitelist",     tags=["whitelist"])
app.include_router(contribution_router, prefix="/api/contribution",  tags=["contribution"])
app.include_router(events_router,       prefix="/api/events",        tags=["events"])
app.include_router(purchase_router,     prefix="/api/purchase",      tags=["purchase"])
app.include_router(jobs_router,         prefix="/api/jobs",          tags=["jobs"])
app.include_router(staking_router,      prefix="/api/staking",       tags=["staking"])
app.include_router(tutorial_router,     prefix="/api/tutorials",     tags=["tutorials"])
app.include_router(announcement_router, prefix="/api/announcements", tags=["announcements"])
app.include_router(faq_router,          prefix="/api/faq",           tags=["faq"])
app.include_router(notification_router, prefix="/api/notifications", tags=["notifications"])
#endregion Routers

# origins = ["*"]
origins = [
    "https://*.ergopad.io",
    "http://54.214.59.165", # alpha
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# catch all route (useful?)
# @app.api_route("/{path_name:path}", methods=["GET"])
# async def catch_all(request: Request, path_name: str):
#     return {"request_method": request.method, "path_name": path_name}

# all requests are timed and logged
@app.middleware("http")
async def add_logging_and_process_time(req: Request, call_next):
    try:
        beg = time.time()
        resNext = await call_next(req)
        tot = str(round((time.time() - beg) * 1000))
        resNext.headers["X-Process-Time-MS"] = tot
        logger.debug(f"""{req.url} | host: {req.client.host}:{req.client.port} | pid {os.getpid()} | {tot}ms""".strip())
        logger.log(LEIF, f"""{req.url}: {tot}ms""".strip())

        # create table api_audit (id serial primary key, request text, host text, port int, application varchar(20), response_time__ms int);
        if AUDIT_REQUESTS:
            sqlAudit = f'''
                insert into api_audit (request, host, port, application, response_time__ms)
                values (:request, :host, :port, 'ergopad', :response_time__ms); 
            '''            
            resAudit = await fetch(sqlAudit, {'request': str(req.url), 'host': req.client.host, 'port': int(req.client.port), 'response_time__ms': int(tot)})

        return resNext

    except Exception as e:
        logger.error(f'ERR:{myself()}: {e}')
        return {'status': 'error', 'message': e}

@app.on_event('startup')
async def startup():
    await init_db()

@app.get('/debug/dbinfo')
async def getDbInfo():
    if not DEBUG:
        return jsonable_encoder({'status': 'invalid', 'message': 'debug'})
    try:
        sql = f'''
            select Inet_server_addr()      as ip_address
                , Version()                as server_version
                , setting                  as server_port
                , current_timestamp :: timestamp
            from pg_settings 
            where name = :name;
        '''
        res = await fetch(sql, {'name': 'port'})
        return jsonable_encoder(res)

    except Exception as e:
        logger.error(f"ERR: {myself()}: {e}")

@app.get("/debug/ping")
async def ping():
    if not DEBUG:
        return jsonable_encoder({'status': 'invalid', 'message': 'debug'})
    return jsonable_encoder({"hello,": "is it me you're looking for?"})

# MAIN
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", reload=True, port=8000)

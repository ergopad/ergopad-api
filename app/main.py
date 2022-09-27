import uvicorn
import logging

from time import time
from os import getpid

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from core.auth import get_current_active_user

from api.v1.routes.users import users_router
from api.v1.routes.auth import auth_router
from api.v1.routes.asset import asset_router
from api.v1.routes.blockchain import blockchain_router
from api.v1.routes.util import util_router
from api.v1.routes.projects import projects_router
from api.v1.routes.vesting import vesting_router
from api.v1.routes.whitelist import whitelist_router
from api.v1.routes.contribution import contribution_router
from api.v1.routes.events import events_router
from api.v1.routes.purchase import purchase_router
from api.v1.routes.jobs import jobs_router
from api.v1.routes.staking import staking_router
from api.v1.routes.announcements import announcement_router
from api.v1.routes.tutorials import tutorial_router
from api.v1.routes.faq import faq_router
from api.v1.routes.notifications import notification_router

app = FastAPI(
    title="ErgoPad",
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

# init database?
# app.add_event_handler("startup", tasks.create_start_app_handler(app))
# app.add_event_handler("shutdown", tasks.create_stop_app_handler(app))

# origins = ["*"]
origins = [
    "https://*.ergopad.io",
    "http://75.155.140.173:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_logging_and_process_time(req: Request, call_next):
    try:
        logging.debug(f"""### REQUEST: {req.url} | host: {req.client.host}:{req.client.port} | pid {getpid()} ###""")
        beg = time()
        resNext = await call_next(req)
        tot = f'{time()-beg:0.3f}'
        resNext.headers["X-Process-Time-MS"] = tot
        logging.debug(f"""### %%% TOOK {tot} / ({req.url}) %%% ###""")
        return resNext

    except Exception as e:
        logging.debug(e)
        return resNext
        pass

# catch all route (useful?)
# @app.api_route("/{path_name:path}", methods=["GET"])
# def catch_all(request: Request, path_name: str):
#     return {"request_method": request.method, "path_name": path_name}

@app.get("/api/ping")
def ping():
    return {"hello": "world"}

# MAIN
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", reload=True, port=8000)

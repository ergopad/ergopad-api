from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
import uvicorn

from api.v1.routes.users import users_router
from api.v1.routes.auth import auth_router
from api.v1.routes.asset import asset_router
from api.v1.routes.blockchain import blockchain_router
from api.v1.routes.util import util_router
from api.v1.routes.projects import projects_router
from api.v1.routes.vesting import vesting_router
from api.v1.routes.whitelist import whitelist_router
from api.v1.routes.events import events_router
from api.v1.routes.assembler import assembler_router
from api.v1.routes.purchase import purchase_router
from api.v1.routes.jobs import jobs_router
# from api.v1.routes.wallets import wallets_router
# from api.v1.routes.tokens import tokens_router

from core import config
# from app.db.session import SessionLocal
from core.auth import get_current_active_user
from core.celery_app import celery_app
from worker import tasks

app = FastAPI(
    title=config.PROJECT_NAME,
    docs_url="/api/docs",
    openapi_url="/api"
)

#region Routers
app.include_router(users_router,      prefix="/api/users",      tags=["users"], dependencies=[Depends(get_current_active_user)])
app.include_router(auth_router,       prefix="/api/auth",       tags=["auth"])
app.include_router(asset_router,      prefix="/api/asset",      tags=["asset"])
app.include_router(blockchain_router, prefix="/api/blockchain", tags=["blockchain"])
app.include_router(projects_router,   prefix="/api/projects",   tags=["projects"])
app.include_router(util_router,       prefix="/api/util",       tags=["util"])
app.include_router(vesting_router,    prefix="/api/vesting",    tags=["vesting"])
app.include_router(whitelist_router,  prefix="/api/whitelist",  tags=["whitelist"])
app.include_router(events_router,     prefix="/api/events",     tags=["events"])
app.include_router(purchase_router,   prefix="/api/purchase",   tags=["purchase"])
app.include_router(assembler_router,  prefix="/api/assembler",  tags=["assembler"])
app.include_router(jobs_router,       prefix="/api/jobs",       tags=["jobs"])
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

# catch all route (useful?)
# @app.api_route("/{path_name:path}", methods=["GET"])
# async def catch_all(request: Request, path_name: str):
#     return {"request_method": request.method, "path_name": path_name}


@app.get("/api/ping")
async def ping():
    return {"hello": "world"}


@app.get("/api/task")
async def example_task():
    celery_app.send_task("tasks.example_task", args=["Hello World"])
    return {"message": "success"}

# MAIN
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", reload=True, port=8000)

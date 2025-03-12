import os
import httpx
import secrets
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from config import settings
from auth import routers as routers_auth
from api import routers as routers_api

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f'{settings.keycloak_openid_host}/realms/{settings.keycloak_openid_realm}/.well-known/openid-configuration')

    app.state.configurations = resp.json()
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(SessionMiddleware, secret_key=secrets.token_urlsafe())

for router in routers_api:
    app.include_router(router, prefix='/api')

for router in routers_auth:
    app.include_router(router, prefix='/auth')

app.mount("/", StaticFiles(directory="public", html=True))

if __name__ == '__main__':
    mode = os.getenv('APP_ENV', 'development')
    uvicorn.run('main:app',
        host = settings.uvicorn_host,
        port = settings.uvicorn_port,
        reload = mode == 'development',
        access_log = mode == 'development'
    )

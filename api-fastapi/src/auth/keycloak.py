import httpx
import urllib.parse
from cachetools import TTLCache
from fastapi import APIRouter, Request, Response, Header
from fastapi.responses import RedirectResponse
from authlib.integrations.starlette_client import OAuth

from config import settings

router = APIRouter(prefix="/keycloak")

oauth = OAuth()

tokenCache = TTLCache(maxsize=256, ttl=60)

oauth.register(
    name="keycloak",
    server_metadata_url=f'{settings.keycloak_openid_host}/realms/{settings.keycloak_openid_realm}/.well-known/openid-configuration',
    client_id=settings.keycloak_client_id,
    client_secret=settings.keycloak_client_secret,
    client_kwargs={"scope": settings.keycloak_openid_scope},
)

@router.get('/configurations')
async def configurations(req: Request):
    return {
        ** req.app.state.configurations,
        'client_id': settings.keycloak_client_id,
    }

@router.get("/callback", name="auth_callback")
async def auth_callback(request: Request, session_state: str):
    tokens = await oauth.keycloak.authorize_access_token(request)
    tokenCache[session_state] = tokens
    query = urllib.parse.urlencode({ 'session_state': session_state })
    return RedirectResponse(f'{settings.url_frontend}/#/keycloak?{query}')

@router.post("/tokens")
async def auth_tokens(request: Request):
    return tokenCache.pop((await request.json())['session_state'], None)

@router.post("/tokens/refresh")
async def auth_tokens_refresh(request: Request):
    async with httpx.AsyncClient() as client:
        resp = await client.post(f'{request.app.state.configurations['token_endpoint']}', data = {
            'client_id': settings.keycloak_client_id,
            'client_secret': settings.keycloak_client_secret,
            'refresh_token': (await request.json())['refresh_token'],
            'grant_type': 'refresh_token',
        })
    return Response(status_code=resp.status_code, content=resp.content)

@router.post("/tokens/revoke")
async def auth_tokens_revoke(request: Request):
    async with httpx.AsyncClient() as client:
        resp = await client.post(f'{request.app.state.configurations['revocation_endpoint']}', data = {
            'client_id': settings.keycloak_client_id,
            'client_secret': settings.keycloak_client_secret,
            **(await request.json())
        })
    return Response(status_code=resp.status_code, content=resp.content)

@router.get("/login")
async def auth_login(request: Request):
    redirect_uri = f'{settings.url_backend}/auth/keycloak/callback'
    return await oauth.keycloak.authorize_redirect(request, redirect_uri)

@router.get("/logout")
def auth_logout(request: Request):
    return RedirectResponse(f'{request.app.state.configurations['end_session_endpoint']}?{request.query_params}')

@router.get("/userinfo")
async def auth_userinfo(request: Request, authorization: str = Header(...)):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f'{request.app.state.configurations['userinfo_endpoint']}', headers={ 'authorization': authorization })
    return Response(status_code=resp.status_code, content=resp.content)

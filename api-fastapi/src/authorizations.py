import httpx
import pydash
from config import settings
from cachetools import TTLCache
from fastapi import Request, HTTPException, Depends
from authlib.jose import jwt, JWTClaims, JoseError

certCache = TTLCache(maxsize=256, ttl=3600)

async def refresh_jwks(request: Request):
    if certCache.get('jwks'):
        return

    async with httpx.AsyncClient() as client:
        resp = await client.get(request.app.state.configurations['jwks_uri'])
        certCache['jwks'] = resp.json()['keys']

async def authorizationRequired(request: Request):
    if not request.headers.get('authorization'):
        raise HTTPException(
            status_code = 401,
            detail="header authorization missing",
        )

    token = request.headers['authorization'].split("Bearer ")[1]
    if not token:
        raise HTTPException(
            status_code = 401,
            detail="Bearer token missing in header authorization",
        )

    await refresh_jwks(request)
    claims = jwt.decode(token, certCache['jwks'], JWTClaims, {
        "iss": {
            "essential": True,
            "value": f'{settings.keycloak_openid_host}/realms/{settings.keycloak_openid_realm}',
        },
        "azp": {
            "essential": True,
            "value": settings.keycloak_client_id,
        },
    })

    try:
        claims.validate()
    except JoseError as e:
        raise HTTPException(status_code = 401, detail=str(e))

    return claims

def claimContainRequired(path: str, target: str):
    async def role_checker(user: dict = Depends(authorizationRequired)):
        roles = pydash.get(user, path, [])
        if target not in roles:
            raise HTTPException(
                status_code = 403,
                detail=f"Insufficient privileges: '{target}' required in path '{path}'."
            )
        return user
    return role_checker

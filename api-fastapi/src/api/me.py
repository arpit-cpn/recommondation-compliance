from typing import Annotated
from fastapi import APIRouter, Request, Depends
from authorizations import authorizationRequired, claimContainRequired

router = APIRouter(prefix="/me")

@router.get('')
async def me(request: Request, user: Annotated[dict, Depends(authorizationRequired)]):
    return user

@router.get('/roles')
async def roles(request: Request, user: Annotated[dict, Depends(claimContainRequired('resource_access.realm-management.roles', 'realm-admin'))]):
    return user

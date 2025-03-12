import time
from os import path
import socket
from fastapi import APIRouter
from config import settings
from fastapi.responses import FileResponse

router = APIRouter()

@router.get('/about')
def about():
    return {
        ** settings.project,
        'hostname': socket.gethostname(),
        'startAt': int(time.time() * 1000),
    }

@router.get('/releases')
def releases():
    return FileResponse('RELEASES.md')

@router.get('/apps')
def apps():
    pth = '../usr/apps.json'
    if path.exists(pth):
        return FileResponse(pth)
    return []

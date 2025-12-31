from fastapi import APIRouter
import logging

logging.basicConfig(level=logging.INFO)
router = APIRouter(prefix='/analysis')

@router.get('/ping')
async def ping():
    return 'pong'
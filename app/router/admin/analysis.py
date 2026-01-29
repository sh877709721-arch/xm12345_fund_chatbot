from fastapi import APIRouter, Depends
import logging
from sqlalchemy.orm import Session

logging.basicConfig(level=logging.INFO)
router = APIRouter(prefix='/analysis')
from app.config.database import get_db
from app.service.rbac import require_admin
from app.schema.auth import UserReadWithRole

@router.get('/ping')
async def ping(db: Session = Depends(get_db),
               _: UserReadWithRole = Depends(require_admin)):
    return 'pong'
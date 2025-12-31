from app.router.admin.knowledge_catalog import router as knowledge_router
from app.router.admin.knowledge_entries import router as knowledge_entries_router
from app.router.admin.knowledge_label import router as knowledge_label_router
from app.router.admin.analysis import router as analysis_router
from app.router.admin.search import router as search_router
from fastapi import APIRouter


import logging


logging.basicConfig(level=logging.INFO)
router = APIRouter(prefix="/admin")

router.include_router(knowledge_router, tags=["knowledge catalog"])
router.include_router(knowledge_entries_router, tags=["knowledge entries"])
router.include_router(knowledge_label_router, tags=["knowledge label"])
router.include_router(analysis_router, tags=["analysis"])
router.include_router(search_router, tags=["search"])
from app.router.admin.knowledge_catalog import router as knowledge_router
from app.router.admin.knowledge_entries import router as knowledge_entries_router
from app.router.admin.knowledge_label import router as knowledge_label_router
from app.router.admin.analysis import router as analysis_router
from app.router.admin.search import router as search_router
from app.router.admin.knowledge_data import router as knowledge_data_router
from app.router.admin.guidelines import router as guidelines_router
from app.router.admin.vote import router as vote_router
from app.router.admin.feedback import router as feedback_router
from app.router.admin.dashboard import router as dashboard_router
from fastapi import APIRouter


import logging


logging.basicConfig(level=logging.INFO)
router = APIRouter(prefix="/admin")

# 管理员专属路由（superadmin, engineer）
router.include_router(knowledge_router, tags=["knowledge catalog"])
router.include_router(knowledge_entries_router, tags=["knowledge entries"])
router.include_router(knowledge_label_router, tags=["knowledge label"])
router.include_router(knowledge_data_router, tags=["knowledge data"])
router.include_router(analysis_router, tags=["analysis"])
router.include_router(search_router, tags=["search"])
router.include_router(guidelines_router, tags=["guidelines"])

# 所有角色可访问的路由（包括 normal_user）
router.include_router(vote_router, tags=["vote"])
router.include_router(feedback_router, tags=["feedback"])
router.include_router(dashboard_router, tags=["dashboard"])

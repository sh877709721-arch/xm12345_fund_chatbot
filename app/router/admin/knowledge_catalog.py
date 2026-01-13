from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Any, Dict
from app.config.database import get_db
from app.service.knowledge_catalog import KnowledgeCatalogService
from app.schema.base import BaseResponse
from app.schema.knowledge import (
    KnowledgeCatalogRead,
)
from app.service.rbac import require_admin
from app.schema.auth import UserReadWithRole
from pydantic import BaseModel
import logging

logging.basicConfig(level=logging.INFO)
router = APIRouter(prefix="/knowledge")

# ###########
# 知识库目录
# ###########

class KnowledgeCatalogRequest(BaseModel):
    id: int
    name: Optional[str]
    catalog_level_1: str
    catalog_level_2: str
    catalog_level_3: str

@router.post("/catalogs", response_model=BaseResponse[KnowledgeCatalogRead])
def create_knowledge_catalog(
    request: KnowledgeCatalogRequest,
    db: Session = Depends(get_db),
    _: UserReadWithRole = Depends(require_admin)
):
    """
    创建知识目录
    
    示例请求:
    POST /knowledge/catalogs
    {
        "name": "医保政策",
        "catalog_level_1": "政策法规",
        "catalog_level_2": "医保政策",
        "catalog_level_3": "门诊报销"
    }
    
    示例响应:
    {
        "code": 200,
        "message": "success",
        "data": {
            "id": 1,
            "category_level_1": "政策法规",
            "category_level_2": "医保政策",
            "category_level_3": "门诊报销",
            "status": "active",
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00"
        }
    }
    """
    id = request.id
    catalog_level_1, catalog_level_2, catalog_level_3 = request.catalog_level_1, request.catalog_level_2, request.catalog_level_3
    if id!=-1:
        raise HTTPException(status_code=400, detail="id参数错误")
    try:
        service = KnowledgeCatalogService(db)
        result = service.create_knowledge_catalog(
            catalog_level_1=catalog_level_1,
            catalog_level_2=catalog_level_2,
            catalog_level_3=catalog_level_3
        )
        return BaseResponse(data=result)
    except Exception as e:
        logging.error(f"创建知识目录失败: {e}")
        raise HTTPException(status_code=500, detail="创建知识目录失败")


@router.get("/catalogs", response_model=BaseResponse[List[KnowledgeCatalogRead]])
def get_knowledge_catalogs(
    db: Session = Depends(get_db),
    _: UserReadWithRole = Depends(require_admin)
):
    """
    获取所有知识目录
    
    示例请求:
    GET /knowledge/catalogs
    
    示例响应:
    {
        "code": 200,
        "message": "success",
        "data": [
            {
                "id": 1,
                "category_level_1": "政策法规",
                "category_level_2": "医保政策",
                "category_level_3": "门诊报销",
                "status": "active",
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        ]
    }
    """
    try:
        service = KnowledgeCatalogService(db)
        result = service.get_knowledge_catalogs()
        return BaseResponse(code= 200, 
                            message="success",
                            data=result)
    except Exception as e:
        logging.error(f"获取知识目录失败: {e}")
        raise HTTPException(status_code=500, detail="获取知识目录失败")


@router.get("/catalog-tree", response_model=BaseResponse[List[Dict[str, Any]]])
def get_knowledge_catalog_tree(
    db: Session = Depends(get_db),
    _: UserReadWithRole = Depends(require_admin)
):
    """
    获取所有知识目录
    
    示例请求:
    GET /knowledge/catalog-tree
    
    示例响应:
    {
        "code": 200,
        "message": "success",
        "data": [
            {
            "职工基本医疗保险": {
                "参保缴费": [
                {
                    "id": 1,
                    "name": "参保对象"
                },
        ],
    }
    """
    try:
        service = KnowledgeCatalogService(db)
        result = service.get_knowledge_catalog_tree()
        return BaseResponse(code= 200, 
                            message="success",
                            data=result)
    except Exception as e:
        logging.error(f"获取知识目录失败: {e}")
        raise HTTPException(status_code=500, detail="获取知识目录失败")


@router.put("/catalogs/{catalog_id}", response_model=BaseResponse[KnowledgeCatalogRead])
def update_knowledge_catalog(
    request: KnowledgeCatalogRequest,
    db: Session = Depends(get_db),
    _: UserReadWithRole = Depends(require_admin)
):
    """
    更新知识目录
    
    示例请求:
    PUT /knowledge/catalogs/1
    {
        "name": "医保政策更新",
        "catalog_level_1": "政策法规",
        "catalog_level_2": "医保政策",
        "catalog_level_3": "住院报销"
    }
    
    示例响应:
    {
        "code": 200,
        "message": "success",
        "data": {
            "id": 1,
            "category_level_1": "政策法规",
            "category_level_2": "医保政策",
            "category_level_3": "住院报销",
            "status": "active",
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-02T00:00:00"
        }
    }
    """
    catalog_id = request.id
    name = request.name
    catalog_level_1 = request.catalog_level_1
    catalog_level_2 = request.catalog_level_2
    catalog_level_3 = request.catalog_level_3
    try:
        service = KnowledgeCatalogService(db)
        result = service.update_knowledge_catalog(
            id=catalog_id,
            catalog_level_1=catalog_level_1,
            catalog_level_2=catalog_level_2,
            catalog_level_3=catalog_level_3
        )
        return BaseResponse(data=result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logging.error(f"更新知识目录失败: {e}")
        raise HTTPException(status_code=500, detail="更新知识目录失败")


@router.delete("/catalogs/{catalog_id}", response_model=BaseResponse[KnowledgeCatalogRead])
def delete_knowledge_catalog(
    catalog_id: int,
    db: Session = Depends(get_db),
    _: UserReadWithRole = Depends(require_admin)
):
    """
    删除知识目录（软删除）
    
    示例请求:
    DELETE /knowledge/catalogs/1
    
    示例响应:
    {
        "code": 200,
        "message": "success",
        "data": {
            "id": 1,
            "category_level_1": "政策法规",
            "category_level_2": "医保政策",
            "category_level_3": "住院报销",
            "status": "deleted",
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-02T00:00:00"
        }
    }
    """
    try:
        service = KnowledgeCatalogService(db)
        result = service.delete_knowledge_catalog(id=catalog_id)
        return BaseResponse(data=result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logging.error(f"删除知识目录失败: {e}")
        raise HTTPException(status_code=500, detail="删除知识目录失败")

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Any, Dict
from app.config.database import get_db
from app.service.knowledge_catalog import KnowledgeCatalogService
from app.schema.base import BaseResponse
from app.schema.knowledge import (
    KnowledgeCatalogRead,
)
from app.service.rbac import require_admin,require_any_role
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
    创建公积金知识目录
    
    示例请求:
    POST /knowledge/catalogs
    {
        "name": "公积金政策",
        "catalog_level_1": "政策法规",
        "catalog_level_2": "公积金政策",
        "catalog_level_3": "购房提取"
    }
    
    示例响应:
    {
        "code": 200,
        "message": "success",
        "data": {
            "id": 1,
            "category_level_1": "政策法规",
            "category_level_2": "公积金政策",
            "category_level_3": "购房提取",
            "status": "active",
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00"
        }
    }
    """
    id = request.id
    catalog_level_1, catalog_level_2, catalog_level_3 = request.catalog_level_1, request.catalog_level_2, request.catalog_level_3
    if id != -1:
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
        logging.error(f"创建公积金知识目录失败: {e}")
        raise HTTPException(status_code=500, detail="创建公积金知识目录失败")


@router.get("/catalogs", response_model=BaseResponse[List[KnowledgeCatalogRead]])
def get_knowledge_catalogs(
    db: Session = Depends(get_db),
    _: UserReadWithRole = Depends(require_any_role)
):
    """
    获取所有公积金知识目录
    
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
                "category_level_2": "公积金政策",
                "category_level_3": "购房提取",
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
        return BaseResponse(
            code=200,
            message="success",
            data=result
        )
    except Exception as e:
        logging.error(f"获取公积金知识目录失败: {e}")
        raise HTTPException(status_code=500, detail="获取公积金知识目录失败")


@router.get("/catalog-tree", response_model=BaseResponse[List[Dict[str, Any]]])
def get_knowledge_catalog_tree(
    db: Session = Depends(get_db),
    _: UserReadWithRole = Depends(require_any_role)
):
    """
    获取所有公积金知识目录树
    
    示例请求:
    GET /knowledge/catalog-tree
    
    示例响应:
    {
        "code": 200,
        "message": "success",
        "data": [
            {
                "公积金缴存业务": {
                    "缴存管理": [
                        {
                            "id": 1,
                            "name": "缴存对象"
                        },
                        {
                            "id": 2,
                            "name": "缴存基数与比例"
                        },
                        {
                            "id": 3,
                            "name": "缴存方式（单位/个人）"
                        },
                        {
                            "id": 4,
                            "name": "缴存变更（增员/减员）"
                        },
                        {
                            "id": 5,
                            "name": "补缴与缓缴规定"
                        },
                        {
                            "id": 6,
                            "name": "缴存纠纷处理"
                        }
                    ],
                    "缴存相关": [
                        {
                            "id": 7,
                            "name": "缴存明细查询"
                        },
                        {
                            "id": 8,
                            "name": "缴存证明开具"
                        },
                        {
                            "id": 9,
                            "name": "汇缴托收办理"
                        },
                        {
                            "id": 10,
                            "name": "退费办理"
                        },
                        {
                            "id": 11,
                            "name": "重复缴存处理"
                        }
                    ],
                    "缴存办理指南": [
                        {
                            "id": 12,
                            "name": "单位缴存登记"
                        },
                        {
                            "id": 13,
                            "name": "个人自愿缴存申请"
                        },
                        {
                            "id": 14,
                            "name": "缴存基数调整办理"
                        },
                        {
                            "id": 15,
                            "name": "单位缴存信息变更"
                        }
                    ]
                }
            },
            {
                "公积金提取业务": {
                    "提取类型": [
                        {
                            "id": 16,
                            "name": "购房提取"
                        },
                        {
                            "id": 17,
                            "name": "租房提取"
                        },
                        {
                            "id": 18,
                            "name": "离职提取"
                        },
                        {
                            "id": 19,
                            "name": "退休提取"
                        },
                        {
                            "id": 20,
                            "name": "代际互助提取"
                        },
                        {
                            "id": 21,
                            "name": "其他提取（出境/大病等）"
                        }
                    ],
                    "提取管理": [
                        {
                            "id": 22,
                            "name": "提取条件"
                        },
                        {
                            "id": 23,
                            "name": "提取额度"
                        },
                        {
                            "id": 24,
                            "name": "提取频次"
                        },
                        {
                            "id": 25,
                            "name": "提取限制"
                        }
                    ],
                    "提取办理指南": [
                        {
                            "id": 26,
                            "name": "提取材料准备"
                        },
                        {
                            "id": 27,
                            "name": "线上提取办理"
                        },
                        {
                            "id": 28,
                            "name": "线下提取办理"
                        },
                        {
                            "id": 29,
                            "name": "提取进度查询"
                        },
                        {
                            "id": 30,
                            "name": "提取到账查询"
                        }
                    ]
                }
            }
        ]
    }
    """
    try:
        service = KnowledgeCatalogService(db)
        result = service.get_knowledge_catalog_tree()
        return BaseResponse(
            code=200,
            message="success",
            data=result
        )
    except Exception as e:
        logging.error(f"获取公积金知识目录树失败: {e}")
        raise HTTPException(status_code=500, detail="获取公积金知识目录树失败")


@router.put("/catalogs/{catalog_id}", response_model=BaseResponse[KnowledgeCatalogRead])
def update_knowledge_catalog(
    request: KnowledgeCatalogRequest,
    db: Session = Depends(get_db),
    _: UserReadWithRole = Depends(require_admin)
):
    """
    更新公积金知识目录
    
    示例请求:
    PUT /knowledge/catalogs/1
    {
        "name": "公积金政策更新",
        "catalog_level_1": "政策法规",
        "catalog_level_2": "公积金政策",
        "catalog_level_3": "购房提取"
    }
    
    示例响应:
    {
        "code": 200,
        "message": "success",
        "data": {
            "id": 1,
            "category_level_1": "政策法规",
            "category_level_2": "公积金政策",
            "category_level_3": "购房提取",
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
        logging.error(f"更新公积金知识目录失败: {e}")
        raise HTTPException(status_code=500, detail="更新公积金知识目录失败")


@router.delete("/catalogs/{catalog_id}", response_model=BaseResponse[KnowledgeCatalogRead])
def delete_knowledge_catalog(
    catalog_id: int,
    db: Session = Depends(get_db),
    _: UserReadWithRole = Depends(require_admin)
):
    """
    删除公积金知识目录（软删除）
    
    示例请求:
    DELETE /knowledge/catalogs/1
    
    示例响应:
    {
        "code": 200,
        "message": "success",
        "data": {
            "id": 1,
            "category_level_1": "政策法规",
            "category_level_2": "公积金政策",
            "category_level_3": "购房提取",
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
        logging.error(f"删除公积金知识目录失败: {e}")
        raise HTTPException(status_code=500, detail="删除公积金知识目录失败")

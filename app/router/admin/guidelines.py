from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.config.database import get_db
from app.service.guidelines import GuidelinesService
from app.schema.base import BaseResponse, PageResponse
from app.schema.guideline import (
    GuidelinesRead,
    GuidelinesCreate,
    GuidelinesUpdate,
    GuidelinesSearchRequest,
    GuidelinesStatusEnum
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/guidelines", tags=["guidelines"])



def get_guideline_service(db: Session = Depends(get_db)) -> GuidelinesService:
    """获取指南服务实例"""
    return GuidelinesService(db)


@router.post("", response_model=BaseResponse[GuidelinesRead])
def create_guideline(
    request: GuidelinesCreate,
    service: GuidelinesService = Depends(get_guideline_service)
):
    """
    创建指南
    """
    try:
        result = service.create_guideline(
            title=request.title,
            condition=request.condition,
            action=request.action,
            prompt_template=request.prompt_template,
            priority=request.priority,
            status=request.status
        )
        service.build_index_by_guideline_id(result.id)
        return BaseResponse(code=200, message="success", data=result)
    except Exception as e:
        logger.error(f"创建指南失败: {e}")
        raise HTTPException(status_code=500, detail="创建指南失败")


@router.post("/search", response_model=BaseResponse[PageResponse[GuidelinesRead]])
def search_guidelines(
    request: GuidelinesSearchRequest,
    service: GuidelinesService = Depends(get_guideline_service)
):
    """
    搜索指南（支持分页、多条件查询和排序）
    """
    try:
        result = service.search_guidelines(
            title=request.title,
            condition=request.condition,
            action=request.action,
            status=request.status,
            priority_min=request.priority_min,
            priority_max=request.priority_max,
            orderby=request.orderby,
            order=request.order,
            page=request.page,
            size=request.size
        )
        return BaseResponse(code=200, message="success", data=result)
    except Exception as e:
        logger.error(f"搜索指南失败: {e}")
        raise HTTPException(status_code=500, detail="搜索指南失败")


@router.get("/{guideline_id}", response_model=BaseResponse[GuidelinesRead])
def get_guideline(
    guideline_id: int,
   service: GuidelinesService = Depends(get_guideline_service)
):
    """
    获取单个指南

    ## 路径参数
    - **guideline_id**: 指南ID

    ## 响应示例
    ```json
    {
        "code": 200,
        "message": "success",
        "data": {
            "id": 1,
            "title": "高血压管理指南",
            "condition": "患者被诊断为高血压",
            "action": "提供高血压管理建议",
            "prompt_template": "基于患者的高血压诊断...",
            "status": "A",
            "created_time": "2025-01-05T10:00:00",
            "updated_time": "2025-01-05T10:00:00"
        }
    }
    ```
    """
    try:
        result = service.get_guideline(guideline_id)
        service.build_index_by_guideline_id(guideline_id)
        if not result:
            raise HTTPException(status_code=404, detail="指南未找到")
        return BaseResponse(code=200, message="success", data=result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取指南失败: {e}")
        raise HTTPException(status_code=500, detail="获取指南失败")


@router.put("/{guideline_id}", response_model=BaseResponse[GuidelinesRead])
def update_guideline(
    guideline_id: int,
    request: GuidelinesUpdate,
    service: GuidelinesService = Depends(get_guideline_service)
):
    """
    更新指南
    """
    try:
        result = service.update_guideline(
            guideline_id=guideline_id,
            title=request.title,
            condition=request.condition,
            action=request.action,
            prompt_template=request.prompt_template,
            priority=request.priority,
            status=request.status
        )
        service.build_index_by_guideline_id(guideline_id)
        return BaseResponse(code=200, message="success", data=result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"更新指南失败: {e}")
        raise HTTPException(status_code=500, detail="更新指南失败")


@router.delete("/{guideline_id}", response_model=BaseResponse[GuidelinesRead])
def delete_guideline(
    guideline_id: int,
    service: GuidelinesService = Depends(get_guideline_service)
):
    """
    删除指南（软删除）

    ## 路径参数
    - **guideline_id**: 指南ID

    ## 响应示例
    ```json
    {
        "code": 200,
        "message": "success",
        "data": {
            "id": 1,
            "title": "高血压管理指南",
            "condition": "患者被诊断为高血压",
            "action": "提供高血压管理建议",
            "prompt_template": "基于患者的高血压诊断...",
            "status": "X",
            "created_time": "2025-01-05T10:00:00",
            "updated_time": "2025-01-05T10:10:00"
        }
    }
    ```
    """
    try:
        result = service.delete_guideline(guideline_id)
        return BaseResponse(code=200, message="success", data=result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"删除指南失败: {e}")
        raise HTTPException(status_code=500, detail="删除指南失败")


@router.get("", response_model=BaseResponse[list[GuidelinesRead]])
def get_all_guidelines(
    service: GuidelinesService = Depends(get_guideline_service)
):
    """
    获取所有未删除的指南列表

    ## 响应示例
    ```json
    {
        "code": 200,
        "message": "success",
        "data": [{
            "id": 1,
            "title": "高血压管理指南",
            "condition": "患者被诊断为高血压",
            "action": "提供高血压管理建议",
            "prompt_template": "基于患者的高血压诊断...",
            "status": "A",
            "created_time": "2025-01-05T10:00:00",
            "updated_time": "2025-01-05T10:00:00"
        }]
    }
    ```
    """
    try:
        result = service.get_guidelines()
        return BaseResponse(code=200, message="success", data=result)
    except Exception as e:
        logger.error(f"获取指南列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取指南列表失败")

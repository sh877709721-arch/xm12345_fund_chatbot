from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.service.feedback import FeedbackService
from app.schema.feedback import FeedbackCreate, FeedbackRead, FeedbackUpdate, ImageUploadResponse
from app.schema.base import BaseResponse, PageResponse
from app.config.database import get_db

router = APIRouter(prefix="/feedback", tags=["feedback"])


def get_feedback_service(db: Session = Depends(get_db)) -> FeedbackService:
    """获取反馈服务实例"""
    return FeedbackService(db)


@router.post("/upload-image", response_model=BaseResponse[ImageUploadResponse])
async def upload_feedback_image(
    file: UploadFile = File(...),
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """
    上传反馈图片

    - **file**: 图片文件 (支持 jpeg, jpg, png, gif, webp 格式，最大5MB)
    """
    try:
        image_info = await feedback_service.upload_image(file)
        return BaseResponse(data=image_info)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图片上传失败: {str(e)}")


@router.post("/", response_model=BaseResponse[FeedbackRead])
async def create_feedback(
    feedback_data: FeedbackCreate,
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """
    创建反馈

    - **content**: 反馈内容
    - **phone**: 联系电话（可选）
    - **images**: 图片列表（可选）
    """
    try:
        print(f"收到的反馈数据: {feedback_data}")  # 调试日志
        feedback = feedback_service.create_feedback(feedback_data)
        return BaseResponse(data=feedback)
    except Exception as e:
        print(f"创建反馈失败: {e}")  # 调试日志
        import traceback
        traceback.print_exc()  # 打印详细错误信息
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=BaseResponse[PageResponse[FeedbackRead]])
async def get_all_feedbacks(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """
    分页获取所有反馈

    - **page**: 页码 (从1开始)
    - **size**: 每页数量 (1-100)
    """
    try:
        feedbacks = feedback_service.get_all_feedbacks(page=page, size=size)
        total = feedback_service.get_total_feedbacks_count()

        page_response = PageResponse(
            items=feedbacks,
            total=total,
            page=page,
            size=size,
            has_next=page * size < total,
            has_prev=page > 1
        )

        return BaseResponse(data=page_response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取反馈列表失败: {str(e)}")


@router.get("/{feedback_id}", response_model=BaseResponse[FeedbackRead])
async def get_feedback(
    feedback_id: int,
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """根据ID获取反馈详情"""
    feedback = feedback_service.get_feedback_by_id(feedback_id)
    if not feedback:
        raise HTTPException(status_code=404, detail="反馈不存在")
    return BaseResponse(data=feedback)


@router.put("/{feedback_id}", response_model=BaseResponse[FeedbackRead])
async def update_feedback(
    feedback_id: int,
    feedback_data: FeedbackUpdate,
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """更新反馈"""
    try:
        feedback = feedback_service.update_feedback(feedback_id, feedback_data)
        if not feedback:
            raise HTTPException(status_code=404, detail="反馈不存在")
        return BaseResponse(data=feedback)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{feedback_id}", response_model=BaseResponse[bool])
async def delete_feedback(
    feedback_id: int,
    feedback_service: FeedbackService = Depends(get_feedback_service)
):
    """删除反馈"""
    try:
        result = feedback_service.delete_feedback(feedback_id)
        if not result:
            raise HTTPException(status_code=404, detail="反馈不存在")
        return BaseResponse(data=result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
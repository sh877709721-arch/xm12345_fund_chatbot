from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
from fastapi import UploadFile, HTTPException
from datetime import datetime

from app.model.feedback import Feedback
from app.schema.feedback import FeedbackCreate, FeedbackUpdate, ImageInfo, ImageUploadResponse


class FeedbackService:
    def __init__(self, db: Session):
        self.db = db

    def create_feedback(self, feedback_data: FeedbackCreate) -> Feedback:
        """创建反馈"""
        print(f"服务层收到的数据: {feedback_data}")  # 调试日志

        try:
            feedback = Feedback(
                content=feedback_data.content,
                phone=feedback_data.phone,
                images=[img.dict() for img in feedback_data.images] if feedback_data.images else None
            )

            print(f"创建的反馈对象: {feedback}")  # 调试日志

            self.db.add(feedback)
            self.db.commit()
            self.db.refresh(feedback)

            print(f"反馈创建成功: {feedback.id}")  # 调试日志
            return feedback

        except Exception as e:
            print(f"数据库操作失败: {e}")  # 调试日志
            import traceback
            traceback.print_exc()  # 打印详细错误信息
            self.db.rollback()
            raise e

    def get_feedback_by_id(self, feedback_id: int) -> Optional[Feedback]:
        """根据ID获取反馈"""
        return self.db.query(Feedback).filter(Feedback.id == feedback_id).first()

    def get_all_feedbacks(self, page: int = 1, size: int = 10) -> List[Feedback]:
        """分页获取所有反馈"""
        offset = (page - 1) * size
        return self.db.query(Feedback).offset(offset).limit(size).all()

    def get_total_feedbacks_count(self) -> int:
        """获取反馈总数"""
        return self.db.query(Feedback).count()

    def update_feedback(self, feedback_id: int, feedback_data: FeedbackUpdate) -> Optional[Feedback]:
        """更新反馈"""
        feedback = self.get_feedback_by_id(feedback_id)
        if not feedback:
            return None

        update_data = feedback_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if field == 'images' and value is not None:
                setattr(feedback, field, [img.dict() for img in value])
            else:
                setattr(feedback, field, value)

        self.db.commit()
        self.db.refresh(feedback)
        return feedback

    def delete_feedback(self, feedback_id: int) -> bool:
        """删除反馈"""
        feedback = self.get_feedback_by_id(feedback_id)
        if not feedback:
            return False

        self.db.delete(feedback)
        self.db.commit()
        return True

    async def upload_image(self, file: UploadFile, upload_dir: str = "uploads/feedback") -> ImageUploadResponse:
        """上传图片文件"""
        # 验证文件类型
        allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型: {file.content_type}。支持的类型: {', '.join(allowed_types)}"
            )

        # 验证文件大小 (最大5MB)
        max_size = 5 * 1024 * 1024  # 5MB
        file_content = await file.read()
        if len(file_content) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超过限制。最大允许: {max_size // (1024 * 1024)}MB"
            )

        # 创建上传目录
        os.makedirs(upload_dir, exist_ok=True)

        # 生成唯一文件名
        file_extension = file.filename.split('.')[-1] if '.' in file.filename else ''
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)

        # 保存文件
        with open(file_path, "wb") as buffer:
            buffer.write(file_content)

        # 构建文件访问URL (相对路径)
        file_url = f"/{upload_dir}/{unique_filename}"

        return ImageUploadResponse(
            url=file_url,
            filename=file.filename,
            size=len(file_content),
            content_type=file.content_type,
            path=file_path
        )
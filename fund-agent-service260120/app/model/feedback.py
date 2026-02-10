from sqlalchemy import Column, String, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import BIGINT, ARRAY
from app.config.database import Base

import datetime


# 反馈功能
class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(BIGINT, primary_key=True, autoincrement=True)
    content = Column(Text, nullable=False)  # 文字反馈内容
    images = Column(JSON, nullable=True)  # 存储图片信息的JSON字段
    phone = Column(Text, nullable=True)
    status = Column(String(255), nullable=False, default='A')
    created_time = Column(DateTime, default=datetime.datetime.now)
    updated_time = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    def add_image(self, image_info: dict):
        """添加图片信息"""
        if self.images is None:
            self.images = []
        self.images.append(image_info)

    def set_images(self, images_list: list):
        """设置图片列表"""
        self.images = images_list

    def get_images(self):
        """获取图片列表"""
        return self.images or []
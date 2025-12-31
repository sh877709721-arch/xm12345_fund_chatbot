from typing import Dict, List, Optional, Any
from pydantic import BaseModel
from datetime import datetime
from app.model.knowledge import KnowledgeStatusEnum





class KnowledgeCatalogRead(BaseModel):
    id: int
    category_level_1: Optional[str]
    category_level_2: Optional[str]
    category_level_3: Optional[str]
    status: KnowledgeStatusEnum
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True


class KnowledgeRead(BaseModel):
    id: int
    knowledge_type: Optional[str]
    name: Optional[str]
    knowledge_catalog_id: Optional[int]
    status: KnowledgeStatusEnum
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class KnowledgeDetailRead(BaseModel):
    id: int
    knowledge_id: int
    content: Optional[str]
    role: Optional[str]
    reference: Optional[str]
    status: KnowledgeStatusEnum
    version: int
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class KnowledgeWithDetailsRead(BaseModel):
    id: int
    knowledge_type: Optional[str]
    name: Optional[str]
    knowledge_catalog_id: Optional[int]
    status: KnowledgeStatusEnum
    created_at: datetime
    updated_at: datetime
    details: Optional[KnowledgeDetailRead]
    catalog: Optional[KnowledgeCatalogRead]
    class Config:
        from_attributes = True



## 标注

class KnowledgeLabelBatchRead(BaseModel):
    id: int
    name: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KnowledgeLabelRead(BaseModel):
    id: int
    name: Optional[str]
    batch_id: int
    status: KnowledgeStatusEnum
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KnowledgeLabelDetailRead(BaseModel):
    id: int
    knowledge_label_id: int
    content: Optional[str]
    context: Optional[str]
    role: Optional[str]
    status: KnowledgeStatusEnum
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True




class KnowledgeLabelWithDetailRead(BaseModel):
    batch_number: int
    label_id: int
    question: Optional[str]
    ai_content: Optional[str]
    user_content: Optional[str]
    is_passed: Optional[bool]
    description: Optional[str]
    filled_by: Optional[str]
    create_at: datetime
    update_at: datetime

    class Config:
        from_attributes = True

from enum import Enum as PyEnum

class PassStateEnum(PyEnum):
    passed = "passed"
    unpassed = "unpassed"
    unchecked = "unchecked"
    all = "all"


class KnowledgeLabelsQueryRequest(BaseModel):
    batch_id: int
    name: Optional[str] = None
    pass_state: Optional[PassStateEnum] = PassStateEnum.unchecked
    filled_by: Optional[str] = None
    page: int = 1
    size: int = 10


class KnowledgeLabelsAndDetailsCreateRequest(BaseModel):
    name: str
    ai_content: str
    user_content: Optional[str]
    description: Optional[str]
    is_passed: Optional[bool]
    filled_by: Optional[str]
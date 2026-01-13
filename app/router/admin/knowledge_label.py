from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.config.database import get_db
from app.service.knowledge_label import KnowledgeLabelService
from app.schema.base import BaseResponse,PageResponse
from app.schema.knowledge import KnowledgeLabelBatchRead, KnowledgeLabelRead, KnowledgeLabelDetailRead,KnowledgeLabelWithDetailRead
from app.model.knowledge import KnowledgeStatusEnum
from app.model.knowledge_label import KnoewledgeRoleEnum
from app.schema.knowledge import KnowledgeLabelsQueryRequest
from app.service.rbac import require_admin
from app.schema.auth import UserReadWithRole


import logging

logging.basicConfig(level=logging.INFO)
router = APIRouter(prefix="/knowledge-label")


"""
    知识测试及标注
    /{batch_id}/{label_id}/{detail_id}

"""




#########################################################################################
###         
###      知识标注批次
###
##########################################################################################
class KnowledgeLabelCreateRequest(BaseModel):
    name: str

class KnowledgeLabelUpdateRequest(BaseModel):
    name: str


# 知识标注批次管理相关路由
@router.post("/batch", response_model=BaseResponse[KnowledgeLabelBatchRead], summary="创建知识标注批次")
def create_knowledge_label_batch(
    req: KnowledgeLabelCreateRequest,
    db: Session = Depends(get_db),
    _: UserReadWithRole = Depends(require_admin)):
    """
    创建一个新的知识标注测试批次
    
    Args:
        name: 批次名称
        db: 数据库会话依赖
        
    Returns:
        KnowledgeLabelBatchRead: 创建的批次信息
    """
    try:
        name = req.name
        service = KnowledgeLabelService(db)
        res  = service.create_knowledge_label_batch(name)
        return BaseResponse(data=res)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/batch", response_model=BaseResponse[List[KnowledgeLabelBatchRead]], summary="获取所有批次")
def get_knowledge_label_batchs(
    db: Session = Depends(get_db),
    _: UserReadWithRole = Depends(require_admin)):
    """
    创建一个新的知识标注测试批次
    
    Args:
        name: 批次名称
        db: 数据库会话依赖
        
    Returns:
        KnowledgeLabelBatchRead: 创建的批次信息
    """
    try:
        service = KnowledgeLabelService(db)
        res  = service.get_knowledge_label_batchs()
        return BaseResponse(data=res)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/batch/{batch_id}", response_model=BaseResponse[KnowledgeLabelBatchRead], summary="更新知识标注批次")
def update_knowledge_label_batch(batch_id: int,
                                 reuqest:KnowledgeLabelUpdateRequest,
                                 db: Session = Depends(get_db),
                                 _: UserReadWithRole = Depends(require_admin)):
    """
    更新指定ID的知识标注批次信息
    
    Args:
        batch_id: 批次ID
        name: 新的批次名称
        db: 数据库会话依赖
        
    Returns:
        KnowledgeLabelBatchRead: 更新后的批次信息
    """
    try:
        name = reuqest.name
        service = KnowledgeLabelService(db)
        db_res = service.update_knowledge_label_batch(batch_id, name)
        return BaseResponse(data=db_res)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/batch/{batch_id}", response_model=BaseResponse[bool], summary="删除知识标注批次")
def delete_knowledge_label_batch(batch_id: int, db: Session = Depends(get_db),
                                 _: UserReadWithRole = Depends(require_admin)):
    """
    删除指定ID的知识标注批次（逻辑删除，将状态设置为deleted）
    
    Args:
        batch_id: 批次ID
        db: 数据库会话依赖
        
    Returns:
        bool: 删除成功返回True
    """
    try:
        service = KnowledgeLabelService(db)
        db_res = service.delete_knowledge_label_batch(batch_id)
        return BaseResponse(data=db_res)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/batch/{batch_id}", response_model=BaseResponse[List[KnowledgeLabelBatchRead]], summary="获取知识标注批次")
def get_knowledge_label_batch(batch_id: int, db: Session = Depends(get_db),
                              _: UserReadWithRole = Depends(require_admin)):
    """
    获取指定ID的知识标注批次信息
    
    Args:
        batch_id: 批次ID
        db: 数据库会话依赖
        
    Returns:
        List[KnowledgeLabelBatchRead]: 批次信息列表
    """
    try:
        service = KnowledgeLabelService(db)
        db_res = service.get_knowledge_label_batch(batch_id)
        return BaseResponse(data=db_res)
    
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))



#########################################################################################
###         
###    知识标注条目
###
##########################################################################################

class KnowledgeLabelRequest(BaseModel):
    name: str

class KnowledgeLabelsRequest(BaseModel):
    names: List[str]    
# 知识标注条目管理相关路由
@router.post("/{batch_id}/label", response_model=BaseResponse[KnowledgeLabelRead], summary="创建知识标注条目")
def create_knowledge_label(batch_id: int,
                           request: KnowledgeLabelRequest,
                           db: Session = Depends(get_db),
                           _: UserReadWithRole = Depends(require_admin)):
    """
    在指定批次中创建一个新的知识标注条目
    
    Args:
        batch_id: 批次ID
        name: 标注条目名称
        db: 数据库会话依赖
        
    Returns:
        KnowledgeLabelRead: 创建的标注条目信息
    """
    try:
        name = request.name
        service = KnowledgeLabelService(db)
        db_res = service.create_knowledge_label(batch_id, name)
        return BaseResponse(data=db_res)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    



# 批量创建知识标注条目
@router.post("/{batch_id}/labels", response_model=BaseResponse[bool], summary="批量创建知识标注条目")
def create_knowledge_labels(batch_id: int,
                            request: KnowledgeLabelsRequest,
                            db: Session = Depends(get_db),
                            _: UserReadWithRole = Depends(require_admin)):
    """
    在指定批次中批量创建知识标注条目
    
    Args:
        batch_id: 批次ID
        names: 标注条目名称列表
        db: 数据库会话依赖
        
    Returns:
        bool: 创建成功返回True
    """
    try:
        names = request.names
        service = KnowledgeLabelService(db)
        db_res = service.create_knowledge_labels(batch_id, names)
        return BaseResponse(data=db_res)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
@router.put("/label/{label_id}", response_model=BaseResponse[KnowledgeLabelRead], summary="更新知识标注条目")
def update_knowledge_label(label_id: int,
                           request: KnowledgeLabelRequest,
                           db: Session = Depends(get_db),
                           _: UserReadWithRole = Depends(require_admin)) -> BaseResponse[KnowledgeLabelRead]:
    """
    更新指定ID的知识标注条目信息
    
    Args:
        label_id: 标注条目ID
        name: 新的标注条目名称
        db: 数据库会话依赖
        
    Returns:
        KnowledgeLabelRead: 更新后的标注条目信息
    """
    try:
        name = request.name
        service = KnowledgeLabelService(db)
        db_res = service.update_knowledge_label(label_id, name)
        return BaseResponse(data=KnowledgeLabelRead.model_validate(db_res))
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/label/{label_id}", response_model=BaseResponse[List[KnowledgeLabelRead]], summary="获取知识标注条目")
def get_knowledge_label(label_id: int, db: Session = Depends(get_db),
                        _: UserReadWithRole = Depends(require_admin)):
    """
    获取指定ID的知识标注条目信息
    
    Args:
        label_id: 标注条目ID
        db: 数据库会话依赖
        
    Returns:
        List[KnowledgeLabelRead]: 标注条目信息列表
    """
    try:
        service = KnowledgeLabelService(db)
        db_res = service.get_knowledge_label(label_id)
        return BaseResponse(data=db_res)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/label/{label_id}", response_model=PageResponse[KnowledgeLabelRead], summary="分页获取知识标注条目")
def get_knowledge_label_pagination(
    page: int = 1,
    size: int = 10,
    db: Session = Depends(get_db),
    _: UserReadWithRole = Depends(require_admin)):
    """
    分页获取知识标注条目信息列表
    
    Args:
        page: 页码（从1开始）
        size: 每页条目数
        db: 数据库会话依赖
        
    Returns:
        List[KnowledgeLabelRead]: 标注条目信息列表
    """
    try:
        service = KnowledgeLabelService(db)
        page_res = service.get_knowledge_label_pagination(page, size)
        return page_res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))




#########################################################################################
###         
###    知识标注详情管理相关路由
###
##########################################################################################



from typing import Optional
class KnowledgeLabelDetailCreateRequest(BaseModel):
    content: str
    context: Optional[str]
    role: KnoewledgeRoleEnum
    status: KnowledgeStatusEnum
    is_passed: Optional[bool]
    description: str
    filled_by: str
@router.post("/{label_id}/detail", response_model=BaseResponse, summary="创建知识标注详情")
def create_knowledge_label_detail(
    label_id: int,
    request: KnowledgeLabelDetailCreateRequest,
    db: Session = Depends(get_db),
    _: UserReadWithRole = Depends(require_admin)
)->BaseResponse:
    """
    创建知识标注详情（回答内容）
    
    Args:
        label_id: 标注条目ID
        content: 详情内容
        role: 角色（system/user/assistant/admin）
        db: 数据库会话依赖
        
    Returns:
        KnowledgeLabelDetailRead: 创建的标注详情信息
    """
    try:
        role = request.role
        service = KnowledgeLabelService(db)
        db_res = service.create_knowledge_label_detail(
            label_id=label_id,
            content=request.content, 
            context= "",
            role= "user",
            status=KnowledgeStatusEnum.pending,
            is_pass=request.is_passed, 
            description=request.description,
            filled_by=request.filled_by)
        return BaseResponse(data=db_res)
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


class KnowledgeLabelDetailUpdateRequest(BaseModel):
    content: str
    context: str
    role: KnoewledgeRoleEnum
    status: KnowledgeStatusEnum
    is_pass: bool
    description: str
    filled_by: str
@router.put("/detail/{detail_id}", response_model=BaseResponse[KnowledgeLabelDetailRead], summary="更新知识标注详情")
def update_knowledge_label_detail(
    detail_id: int,
    request: KnowledgeLabelDetailUpdateRequest,
    db: Session = Depends(get_db),
    _: UserReadWithRole = Depends(require_admin)
):
    """
    更新知识标注详情信息
    
    Args:
        detail_id: 标注条目ID
        content: 详情内容
        context: 上下文信息
        role: 角色
        status: 状态
        is_pass: 是否通过审核
        description: 描述信息
        filled_by: 填写人
        db: 数据库会话依赖
        
    Returns:
        KnowledgeLabelDetailRead: 更新后的标注详情信息
    """
    try:
        
        content = request.content
        context = request.context
        role = request.role
        status = request.status
        is_pass = request.is_pass
        description = request.description
        filled_by = request.filled_by
        service = KnowledgeLabelService(db)
        db_res = service.update_knowledge_label_detail(
            detail_id, content, context, role.value, status, is_pass, description, filled_by
        )
        return BaseResponse(data=db_res)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    


@router.delete("/detail/{detail_id}", response_model=BaseResponse, summary="更新知识标注详情")
def delete_knowledge_label_detail(
    detail_id: int,
    db: Session = Depends(get_db),
    _: UserReadWithRole = Depends(require_admin)
):
    """
    更新知识标注详情信息
    
    Args:
        detail_id: 标注条目ID
        content: 详情内容
        context: 上下文信息
        role: 角色
        status: 状态
        is_pass: 是否通过审核
        description: 描述信息
        filled_by: 填写人
        db: 数据库会话依赖
        
    Returns:
        KnowledgeLabelDetailRead: 更新后的标注详情信息
    """
    try:
        service = KnowledgeLabelService(db)
        db_res = service.delete_knowledge_label_detail(
            detail_id
        )
        return BaseResponse(data=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


#########################################################################################
###         
###    查询清单
###
##########################################################################################


@router.post("/query", response_model=BaseResponse[PageResponse[KnowledgeLabelWithDetailRead]], summary="查询知识标注条目")
def query_knowledge_labels_details(
        request: KnowledgeLabelsQueryRequest,
        db: Session = Depends(get_db),
        _: UserReadWithRole = Depends(require_admin))->BaseResponse[PageResponse[KnowledgeLabelWithDetailRead]]:
    """
    查询知识标注条目
    
    Args:
        name: 名称
        page: 页码（从1开始）
        size: 每页条目数
        db: 数据库会话依赖
        
    Returns:
        List[KnowledgeLabelRead]: 匹配的标注条目信息列表
    """

    try: 
        service = KnowledgeLabelService(db)
        page_res = service.query_knowledge_labels_details(
            request.batch_id,
            request.name,
            request.pass_state,
            request.filled_by,
            request.page,
            request.size
        )

        return BaseResponse(data=page_res)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

#########################################################################################
###         
###    同时创建\更新 知识条目及标注
###
##########################################################################################


from app.schema.knowledge import KnowledgeLabelsAndDetailsCreateRequest
@router.post("/{batch_id}/label-detail", response_model=BaseResponse, summary="创建知识条目及标注")
def create_knowledge_labels_and_details(
    batch_id: int,
    request: KnowledgeLabelsAndDetailsCreateRequest,
    db: Session = Depends(get_db),
    _: UserReadWithRole = Depends(require_admin)
)->BaseResponse:
    """
    同时创建知识条目及标注
    
    Args:
        batch_id: 批次ID
        request: 创建请求参数
        db: 数据库会话依赖
        
    Returns:
        List[KnowledgeLabelWithDetailRead]: 创建的标注条目信息列表
    """
    try: 
        service = KnowledgeLabelService(db)
        db_res = service.create_knowledge_label(batch_id, request.name)
        

        # 新增AI回答
        ai_res = service.create_knowledge_label_detail(label_id=db_res.id, 
                                              content=request.ai_content, 
                                              context= "" ,
                                              role="assistant", 
                                              status=KnowledgeStatusEnum.active, 
                                              is_pass=request.is_passed, 
                                              description=request.description, 
                                              filled_by="assistant")
        # 新增用户标注
        user_res = service.create_knowledge_label_detail(label_id=db_res.id, 
                                              content=request.user_content, 
                                              context= "" ,
                                              role="user", 
                                              status=KnowledgeStatusEnum.active, 
                                              is_pass=request.is_passed, 
                                              description=request.description, 
                                              filled_by=request.filled_by)

        return BaseResponse(data=[ai_res, user_res])


    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{label_id}/label-detail", response_model=BaseResponse, summary="创建知识条目及标注")
def update_knowledge_labels_and_details(
    label_id: int,
    request: KnowledgeLabelsAndDetailsCreateRequest,
    db: Session = Depends(get_db),
    _: UserReadWithRole = Depends(require_admin)
)->BaseResponse:
    """
    同时创建知识条目及标注
    
    Args:
        batch_id: 批次ID
        request: 创建请求参数
        db: 数据库会话依赖
        
    Returns:
        List[KnowledgeLabelWithDetailRead]: 创建的标注条目信息列表
    """
    try: 
        service = KnowledgeLabelService(db)
        db_res = service.update_knowledge_label(label_id, request.name)
        

        # 新增AI回答
        ai_res = service.create_knowledge_label_with_detail(label_id=db_res.id, 
                                              content=request.ai_content, 
                                              context= "" ,
                                              role="assistant", 
                                              status=KnowledgeStatusEnum.active, 
                                              is_pass=request.is_passed, 
                                              description=request.description, 
                                              filled_by="assistant")
        # 新增用户标注
        user_res = service.create_knowledge_label_with_detail(label_id=db_res.id, 
                                              content=request.user_content, 
                                              context= "" ,
                                              role="user", 
                                              status=KnowledgeStatusEnum.active, 
                                              is_pass=request.is_passed, 
                                              description=request.description, 
                                              filled_by=request.filled_by)

        return BaseResponse(data=[ai_res, user_res])


    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


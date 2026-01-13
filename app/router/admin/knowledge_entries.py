from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from app.config.database import get_db
from app.service.knowledge_entries import KnowledgeService
from app.service.knowledge_catalog import KnowledgeCatalogService
from app.service.knowledge_index import KnowledgeIndexService
from app.service.knowledge_data_index import KnowledgeDataIndexService
from app.schema.base import BaseResponse,PageResponse
from app.schema.knowledge import (
    KnowledgeRead,
    KnowledgeDetailRead,
    KnowledgeWithDetailsRead,
    ExcelUploadResponse,
    KnowledgeDataSearchRequest,
    KnowledgeDataSearchResponse
)
from app.model.knowledge import KnowledgeTypeEnum, KnowledgeStatusEnum
from pydantic import BaseModel
import logging
from app.service.rbac import require_admin
from app.schema.auth import UserReadWithRole

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
router = APIRouter(prefix="/knowledge")


# ###############
# 内部辅助函数
# ###############

def _process_excel_upload(
    knowledge_id: int,
    file_content: bytes,
    filename: str | None,
    db: Session
) -> Dict[str, Any]:
    """
    处理 Excel 文件上传的内部函数（封装通用逻辑）

    Args:
        knowledge_id: 知识ID
        file_content: 文件内容（字节）
        filename: 文件名
        db: 数据库会话

    Returns:
        处理结果字典

    Raises:
        ValueError: 文件类型不正确
    """
    # 验证文件类型
    if not filename or not filename.endswith(('.xlsx', '.xls')):
        raise ValueError("仅支持 .xlsx 或 .xls 格式")

    logger.info(f"📤 开始处理 Excel 上传:")
    logger.info(f"  - knowledge_id: {knowledge_id}")
    logger.info(f"  - 文件名: {filename}")
    logger.info(f"  - 文件大小: {len(file_content)} bytes")

    # 处理上传
    service = KnowledgeDataIndexService(db)
    result = service.process_excel_upload(
        knowledge_id=knowledge_id,
        file_content=file_content
    )

    logger.info(f"✅ Excel 上传成功:")
    logger.info(f"  - knowledge_data_id: {result['knowledge_data_id']}")
    logger.info(f"  - 处理行数: {result['rows_processed']}")
    logger.info(f"  - 列数: {result['columns']}")

    return result

# ###########
# 知识库 实体本身
# ###########

class KnowledgeDetailSchema(BaseModel):
    content: str
    role: str
    reference: Optional[str] = None
    status: KnowledgeStatusEnum = KnowledgeStatusEnum.pending
    created_by: Optional[int] = None
    version: Optional[int] = None

class KnowledgeRequest(BaseModel):
    knowledge_type: KnowledgeTypeEnum
    knowledge_catalog_id: int
    name: str
    details: KnowledgeDetailSchema
    created_by: Optional[int] = None

    

@router.post("/entries", response_model=BaseResponse[KnowledgeRead])
def create_knowledge(
    request: KnowledgeRequest,
    db: Session = Depends(get_db),
    _: UserReadWithRole = Depends(require_admin)
):
    """
    创建知识条目
    
    示例请求:
    POST /knowledge/entries
    {
        "knowledge_type": "qa",
        "knowledge_catalog_id": 1,
        "name": "门诊报销政策问答",
        "details": {
            "content": "string",
            "role": "string",
            "status": "pending",
            "created_by": 0,
            "version": 0
        },
        "created_by": 1001
    }
    
    示例响应:
    {
        "code": 200,
        "message": "success",
        "data": {
            "id": 1,
            "knowledge_type": "qa",
            "name": "门诊报销政策问答",
            "knowledge_catalog_id": 1,
            "status": "active",
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00"
        }
    }
    """
    
    knowledge_type = request.knowledge_type
    knowledge_catalog_id = request.knowledge_catalog_id
    name = request.name
    # TODO: 在创建用户系统后进行修改, role 也应当进行修改
    created_by = request.created_by
    
    try:
        service = KnowledgeService(db)
        result = service.create_knowledge(
            knowledge_type=knowledge_type,
            knowledge_catalog_id=knowledge_catalog_id,
            name=name,
            status=KnowledgeStatusEnum.pending,
            created_by=created_by
        )
        service.create_knowledge_detail(
            knowledge_id=result.id,
            content=request.details.content,
            role=request.details.role,
            reference=request.details.reference,
            status=KnowledgeStatusEnum.pending,
            created_by=request.details.created_by
        )

        return BaseResponse(
            code=200,
            message="success",
            data=result)
    
    except Exception as e:
        logging.error(f"创建知识条目失败: {e}")
        raise HTTPException(status_code=500, detail="创建知识条目失败")



class KnowledgeSearchRequest(BaseModel):
    knowledge_type: Optional[KnowledgeTypeEnum] = None
    catalog_level_1: Optional[str] = None
    catalog_level_2: Optional[str] = None
    catalog_level_3: Optional[str] = None
    status: Optional[str] = None
    name: Optional[str] = None
    orderby: str = "id"  # 支持的值: 'id', 'created_at', 'updated_at'
    order: str = "desc"  # 新增：支持 'asc' 或 'desc'，默认降序
    page: int = 1
    size: int = 10
@router.post("/entries/search", response_model=BaseResponse[PageResponse[KnowledgeWithDetailsRead]])
def get_knowledges(
    request: KnowledgeSearchRequest,
    db: Session = Depends(get_db),
    _: UserReadWithRole = Depends(require_admin)
):
    """
    搜索知识条目（支持分页和多条件查询）

    查询参数:
    - knowledge_catalog_id: 知识目录ID
    - knowledge_type: 知识类型
    - name: 知识名称（模糊匹配）
    - orderby: 排序字段，支持 'id', 'created_at', 'updated_at'，默认为 'id'（降序）
    - order: 排序方向，支持 'asc'（升序）或 'desc'（降序），默认为 'desc'
    - page: 页码（从1开始）
    - size: 每页大小

    示例请求:
    POST /knowledge/entries/search
    {
        "orderby": "updated_at",
        "page": 1,
        "size": 10
    }
    
    示例响应:
    {
        "code": 200,
        "message": "success",
        "data": {
            "items": [
                {
                    "id": 1,
                    "knowledge_type": "qa",
                    "name": "门诊报销政策问答",
                    "knowledge_catalog_id": 1,
                    "status": "active",
                    "created_at": "2023-01-01T00:00:00",
                    "updated_at": "2023-01-01T00:00:00",
                    "details": [
                        {
                            "id": 1,
                            "knowledge_id": 1,
                            "content": "门诊报销政策内容...",
                            "role": "assistant",
                            "status": "active",
                            "version": 1,
                            "created_at": "2023-01-01T00:00:00",
                            "updated_at": "2023-01-01T00:00:00"
                        }
                    ]
                }
            ],
            "total": 1,
            "page": 1,
            "size": 10,
            "has_next": false,
            "has_prev": false
        }
    }
    """

    catalog_level_1 = request.catalog_level_1
    catalog_level_2 = request.catalog_level_2
    catalog_level_3 = request.catalog_level_3
    knowledge_type = request.knowledge_type
    name = request.name
    page = request.page
    size = request.size
    knowledge_status = request.status
    try:
        # 根据  catalog_level_1 catalog_level_2 catalog_level_3 获取知识目录ID
        catalog_service = KnowledgeCatalogService(db)
        db_catalog = catalog_service.get_knowledge_catalog_by_level(
            level_1=catalog_level_1,
            level_2=catalog_level_2,
            level_3=catalog_level_3
            )
        knowledge_catalog_id = []
        for item in db_catalog:
            knowledge_catalog_id.append(item.id)

        service = KnowledgeService(db)
        result = service.search_knowledges(
            knowledge_catalog_id=knowledge_catalog_id,
            knowledge_type=knowledge_type,
            knowledge_status=knowledge_status,
            name=name,
            orderby=request.orderby,
            order=request.order,
            page=page,
            size=size
        )
        return BaseResponse(
            code=200,
            message="success",
            data=result
        )
    except Exception as e:
        logging.error(f"获取知识条目失败: {e}")
        raise HTTPException(status_code=500, detail="获取知识条目失败")


class KnowledgeUpdateRequest(BaseModel):
    knowledge_type: KnowledgeTypeEnum
    knowledge_catalog_id: int
    name: str
    details: Optional[KnowledgeDetailSchema] = None

@router.put("/entries/{knowledge_id}", response_model=BaseResponse[KnowledgeRead])
def update_knowledge(
    knowledge_id: int,
    request: KnowledgeUpdateRequest,
    #file: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    _: UserReadWithRole = Depends(require_admin)
):
    """
    更新知识条目
    
    示例请求:
    PUT /knowledge/entries/1
    {
        "knowledge_type": "document",
        "knowledge_catalog_id": 1,
        "name": "门诊报销政策文档",
        "details": {
            "content": "更新后的知识内容",
            "role": "assistant",
            "status": "active",
            "created_by": 1
        }
    }
    
    示例响应:
    {
        "code": 200,
        "message": "success",
        "data": {
            "id": 1,
            "knowledge_type": "document",
            "name": "门诊报销政策文档",
            "knowledge_catalog_id": 1,
            "status": "active",
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-02T00:00:00"
        }
    }
    """
    try:
        service = KnowledgeService(db)
        status = KnowledgeStatusEnum.pending 
        # 如果提供了详情，则更新详情
        if request.details:

            status = request.details.status
            service.delete_knowledge_detail(knowledge_id)
            service.create_knowledge_detail(
                knowledge_id=knowledge_id,
                content=request.details.content,
                role=request.details.role,
                reference=request.details.reference,
                status=request.details.status,
                created_by=request.details.created_by
                )
            status = request.details.status
                                # 更新基本信息
        
        indexed = KnowledgeIndexService(db)

        # 已经索引的知识状态 status 置为 'P'
        try:
            pending_result = indexed.update_knowledge_pending_by_id(knowledge_id)
            logger.info(f"Knowledge {knowledge_id} indexed status updated to pending: {pending_result}")
            if status == KnowledgeStatusEnum.active:
                # 新增一条查询
                indexed.add_knowledge_active_by_id(knowledge_id)
        except Exception as e:
            logger.warning(f"Failed to update indexed knowledge to pending: {e}")
            # 不阻塞主流程，只是记录警告

        # 处理文件上传（如果提供）
        # if file:
        #     try:
        #         # 读取文件内容（同步方式）
        #         file_content = file.file.read()

        #         # 调用封装的上传处理函数
        #         result = _process_excel_upload(
        #             knowledge_id=knowledge_id,
        #             file_content=file_content,
        #             filename=file.filename,
        #             db=db
        #         )
        #         logger.info(f"✅ 更新时 Excel 上传成功: {result['rows_processed']} 行数据")
        #     except ValueError as e:
        #         logger.warning(f"⚠️ Excel 上传参数错误: {e}")
        #         raise HTTPException(status_code=400, detail=str(e))
        #     except Exception as e:
        #         logger.error(f"❌ Excel 上传失败: {e}", exc_info=True)
        #         raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

        # 更新知识基本信息
        result = service.update_knowledge(
            id=knowledge_id,
            knowledge_type=request.knowledge_type,
            knowledge_catalog_id=request.knowledge_catalog_id,
            status=status,
            name=request.name
        )
        
        return BaseResponse(data=result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logging.error(f"更新知识条目失败: {e}")
        raise HTTPException(status_code=500, detail="更新知识条目失败")


@router.delete("/entries/{knowledge_id}", response_model=BaseResponse[KnowledgeRead])
def delete_knowledge(knowledge_id: int, db: Session = Depends(get_db),
                      _: UserReadWithRole = Depends(require_admin)):
    """
    删除知识条目（软删除）
    
    示例请求:
    DELETE /knowledge/entries/1
    
    示例响应:
    {
        "code": 200,
        "message": "success",
        "data": {
            "id": 1,
            "knowledge_type": "document",
            "name": "门诊报销政策文档",
            "knowledge_catalog_id": 1,
            "status": "deleted",
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-02T00:00:00"
        }
    }
    """
    try:
        service = KnowledgeService(db)
        result = service.delete_knowledge(id=knowledge_id)
        return BaseResponse(data=result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logging.error(f"删除知识条目失败: {e}")
        raise HTTPException(status_code=500, detail="删除知识条目失败")


@router.post("/details", response_model=BaseResponse[KnowledgeDetailRead])
def create_knowledge_detail(
    knowledge_id: int,
    content: str,
    reference: str,
    role: str,
    status: KnowledgeStatusEnum = KnowledgeStatusEnum.active,
    created_by: Optional[int] = None,
    db: Session = Depends(get_db),
    _: UserReadWithRole = Depends(require_admin)
):
    """
    创建知识详情（支持版本管理）
    
    示例请求:
    POST /knowledge/details
    {
        "knowledge_id": 1,
        "content": "门诊报销政策内容...",
        "role": "assistant",
        "status": "active",
        "created_by": 1001
    }
    
    示例响应:
    {
        "code": 200,
        "message": "success",
        "data": {
            "id": 1,
            "knowledge_id": 1,
            "content": "门诊报销政策内容...",
            "role": "assistant",
            "status": "active",
            "version": 1,
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-01T00:00:00"
        }
    }
    """
    try:
        service = KnowledgeService(db)
        result = service.create_knowledge_detail(
            knowledge_id=knowledge_id,
            content=content,
            reference=reference,
            role=role,
            status=status,
            created_by=created_by
        )
        return BaseResponse(data=result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logging.error(f"创建知识详情失败: {e}")
        raise HTTPException(status_code=500, detail="创建知识详情失败")


@router.get("/details/{knowledge_id}", response_model=BaseResponse[List[KnowledgeDetailRead]])
def get_knowledge_details(knowledge_id: int, db: Session = Depends(get_db),
                           _: UserReadWithRole = Depends(require_admin)):
    """
    获取知识详情列表（按版本倒序）
    
    示例请求:
    GET /knowledge/details/1
    
    示例响应:
    {
        "code": 200,
        "message": "success",
        "data": [
            {
                "id": 2,
                "knowledge_id": 1,
                "content": "门诊报销政策更新内容...",
                "role": "assistant",
                "status": "active",
                "version": 2,
                "created_at": "2023-01-02T00:00:00",
                "updated_at": "2023-01-02T00:00:00"
            },
            {
                "id": 1,
                "knowledge_id": 1,
                "content": "门诊报销政策内容...",
                "role": "assistant",
                "status": "inactive",
                "version": 1,
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        ]
    }
    """
    try:
        service = KnowledgeService(db)
        result = service.get_knowledge_details(knowledge_id=knowledge_id)
        return BaseResponse(data=result)
    except Exception as e:
        logging.error(f"获取知识详情失败: {e}")
        raise HTTPException(status_code=500, detail="获取知识详情失败")


@router.put("/details/{detail_id}", response_model=BaseResponse[KnowledgeDetailRead])
def update_knowledge_detail(
    detail_id: int,
    content: str,
    db: Session = Depends(get_db),
    _: UserReadWithRole = Depends(require_admin)
):
    """
    更新知识详情
    
    示例请求:
    PUT /knowledge/details/1
    {
        "content": "更新后的门诊报销政策内容..."
    }
    
    示例响应:
    {
        "code": 200,
        "message": "success",
        "data": {
            "id": 1,
            "knowledge_id": 1,
            "content": "更新后的门诊报销政策内容...",
            "role": "assistant",
            "status": "active",
            "version": 1,
            "created_at": "2023-01-01T00:00:00",
            "updated_at": "2023-01-03T00:00:00"
        }
    }
    """
    try:
        service = KnowledgeService(db)
        result = service.update_knowledge_detail(detail_id=detail_id, content=content)
        return BaseResponse(data=result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logging.error(f"更新知识详情失败: {e}")
        raise HTTPException(status_code=500, detail="更新知识详情失败")


@router.delete("/details/{knowledge_id}", response_model=BaseResponse[bool])
def delete_knowledge_detail(knowledge_id: int, db: Session = Depends(get_db),
                             _: UserReadWithRole = Depends(require_admin)):
    """
    删除知识详情

    示例请求:
    DELETE /knowledge/details/1

    示例响应:
    {
        "code": 200,
        "message": "success",
        "data": true
    }
    """
    try:
        service = KnowledgeService(db)
        result = service.delete_knowledge_detail(knowledge_id=knowledge_id)
        if not result:
            raise HTTPException(status_code=404, detail="知识详情未找到")
        return BaseResponse(data=result)
    except Exception as e:
        logging.error(f"删除知识详情失败: {e}")
        raise HTTPException(status_code=500, detail="删除知识详情失败")


# ###########
# Excel 数据上传和搜索
# ###########

@router.post("/upload-excel", response_model=BaseResponse[ExcelUploadResponse])
def upload_excel(
    knowledge_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: UserReadWithRole = Depends(require_admin)
):
    """
    上传 Excel 文件并创建索引

    Args:
        knowledge_id: 知识ID
        file: Excel 文件（.xlsx 或 .xls）

    示例请求:
    POST /knowledge/upload-excel?knowledge_id=1
    Content-Type: multipart/form-data
    file: <Excel 文件>

    示例响应:
    {
        "code": 200,
        "message": "success",
        "data": {
            "status": "success",
            "knowledge_data_id": 1,
            "rows_processed": 100,
            "columns": 5,
            "message": "Excel 上传成功，处理了 100 行数据"
        }
    }
    """
    try:
        # 验证文件名
        if not file.filename:
            raise HTTPException(status_code=400, detail="文件名不能为空")

        # 读取文件内容（同步方式）
        file_content = file.file.read()

        # 调用封装的上传处理函数
        result = _process_excel_upload(
            knowledge_id=knowledge_id,
            file_content=file_content,
            filename=file.filename,
            db=db
        )

        result['message'] = f"Excel 上传成功，处理了 {result['rows_processed']} 行数据"

        return BaseResponse(data=result)

    except ValueError as e:
        logger.warning(f"⚠️ Excel 上传参数错误: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Excel 上传失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.post("/search-data", response_model=BaseResponse[KnowledgeDataSearchResponse])
def search_knowledge_data(
    request: KnowledgeDataSearchRequest,
    db: Session = Depends(get_db),
    _: UserReadWithRole = Depends(require_admin)
):
    """
    搜索知识数据（Excel 表格数据）

    示例请求:
    POST /knowledge/search-data
    {
        "knowledge_id": 1,
        "query": "技术部",
        "top_n": 10
    }

    示例响应:
    {
        "code": 200,
        "message": "success",
        "data": {
            "results": [
                {
                    "row": {"姓名": "张三", "年龄": 25, "部门": "技术部", "职位": "工程师"},
                    "score": 0.95,
                    "knowledge_data_id": 1
                }
            ],
            "count": 1
        }
    }
    """
    try:
        service = KnowledgeDataIndexService(db)
        results = service.search_knowledge_data(
            knowledge_id=request.knowledge_id,
            query=request.query,
            top_n=request.top_n
        )

        response = KnowledgeDataSearchResponse(
            results=results,
            count=len(results)
        )

        return BaseResponse(data=response)
    except Exception as e:
        logging.error(f"❌ 搜索知识数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))




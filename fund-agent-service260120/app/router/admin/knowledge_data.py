from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import  Dict, Any
from app.config.database import get_db
from app.service.knowledge_data_index import KnowledgeDataIndexService
from app.schema.base import BaseResponse
from app.schema.knowledge import (
    ExcelUploadResponse,
    KnowledgeDataSearchRequest,
    KnowledgeDataSearchResponse,
    DataTableSearchRequest,
    DataTableSearchResponse,
    DataTableRowResult,
    DataTableSearchResult,
    KnowledgeDetailInfo
)
import logging
from app.service.rbac import require_admin,require_any_role
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


@router.post("/search-knowledge-data", response_model=BaseResponse[DataTableSearchResponse])
def search_data_table(
    request: DataTableSearchRequest,
    db: Session = Depends(get_db),
    _: UserReadWithRole = Depends(require_any_role)
):
    """
    搜索数据表格（跨所有 knowledge_id）

    示例请求:
    POST /knowledge/search-knowledge-data
    {
        "query": "输入诊所名称、药名",
        "top_n": 10,
        "threshold": 0.7
    }

    示例响应:
    {
        "code": 200,
        "message": "success",
        "data": {
            "results": [
                {
                    "table_data": {
                        "row": {"疾病名称": "高血压", "症状": "头晕", "治疗方案": "降压药"},
                        "score": 0.95,
                        "knowledge_data_id": 123
                    },
                    "knowledge_detail": {
                        "knowledge_id": 1,
                        "content": "高血压是一种常见的慢性疾病...",
                        "reference": "https://example.com",
                        "version": 2
                    }
                }
            ],
            "count": 1
        }
    }
    """
    try:
        from app.service.knowledge_entries import KnowledgeService

        # 1. 向量搜索表格数据（搜索所有 knowledge_id）
        index_service = KnowledgeDataIndexService(db)
        search_results = index_service.search_knowledge_data_vector(
            knowledge_id=None,  # 搜索所有表格
            query=request.query,
            threshold=request.threshold,
            top_n=request.top_n
        )

        if not search_results:
            return BaseResponse(data=DataTableSearchResponse(results=[], count=0))

        # 2. 按 knowledge_id 分组并获取详情
        knowledge_service = KnowledgeService(db)
        knowledge_detail_map = {}  # {knowledge_id: detail}

        # 去重：提取所有唯一的 knowledge_id
        unique_knowledge_ids = list(set(
            result['knowledge_id'] for result in search_results
        ))

        # 批量获取详情
        for kid in unique_knowledge_ids:
            try:
                details = knowledge_service.get_knowledge_details(kid)
                if details:
                    # 取最新版本的详情
                    knowledge_detail_map[kid] = details[0]
                else:
                    knowledge_detail_map[kid] = None
            except Exception as e:
                logger.error(f"获取 knowledge_id={kid} 的详情失败: {e}")
                knowledge_detail_map[kid] = None

        # 3. 组合结果
        combined_results = []
        for result in search_results:
            kid = result['knowledge_id']
            detail = knowledge_detail_map.get(kid)

            # 构造知识详情信息
            detail_info = KnowledgeDetailInfo(
                knowledge_id=kid,
                content=detail.content if detail else None,
                reference=detail.reference if detail else None,
                version=detail.version if detail else None
            )

            # 构造表格数据结果
            table_data = DataTableRowResult(
                row=result['row'],
                score=result['score'],
                knowledge_data_id=result['knowledge_data_id']
            )

            # 组合完整结果
            combined_results.append(DataTableSearchResult(
                table_data=table_data,
                knowledge_detail=detail_info
            ))

        response = DataTableSearchResponse(
            results=combined_results,
            count=len(combined_results)
        )

        return BaseResponse(data=response)

    except Exception as e:
        logger.error(f"❌ 搜索数据表格失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))




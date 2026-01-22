from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.service.vote import VoteService
from app.schema.vote import VoteCreate, VoteRead, VoteStats, VoteUpdate, VoteWithMessage
from app.schema.base import BaseResponse, PageResponse
from app.config.database import get_db
from app.service.rbac import require_any_role
from app.schema.auth import UserReadWithRole

router = APIRouter(prefix="/vote", tags=["vote"])


def get_vote_service(db: Session = Depends(get_db)) -> VoteService:
    """获取投票服务实例"""
    return VoteService(db)


@router.post("/", response_model=BaseResponse[VoteRead])
async def create_vote(
    vote_data: VoteCreate,
    vote_service: VoteService = Depends(get_vote_service)
):
    """
    创建投票

    - **message_id**: 消息ID
    - **vote_type**: 投票类型 (good/average/poor)
    """
    try:
        vote = vote_service.create_vote(vote_data)
        return BaseResponse(data=vote)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/with_messages", response_model=BaseResponse[PageResponse[VoteWithMessage]])
async def get_votes_with_messages(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=1000, description="每页数量"),
    vote_type: Optional[str] = Query(None, description="投票类型过滤 (good/medium/bad)"),
    start_date: Optional[datetime] = Query(None, description="开始时间 (YYYY-MM-DD HH:MM:SS)"),
    end_date: Optional[datetime] = Query(None, description="结束时间 (YYYY-MM-DD HH:MM:SS)"),
    searchKeyword: Optional[str] = Query(None, description="搜索关键词（搜索问题和回答）"),
    client_type: Optional[str] = Query(None, description="请求来源过滤 (web/h5/miniprogram/mp/公积金/rexian)"),
    vote_service: VoteService = Depends(get_vote_service),
    current_user: UserReadWithRole = Depends(require_any_role)
):
    """
    获取带问题和答案的投票列表（支持按类型和时间过滤）

    - **vote_type**: 投票类型过滤 (good/medium/bad)
    - **start_date**: 开始时间过滤
    - **end_date**: 结束时间过滤
    - **searchKeyword**: 搜索关键词（搜索问题和回答）
    - **client_type**: 请求来源过滤 (web/h5/miniprogram/mp/公积金/rexian)
    """
    from app.model.vote import VoteEnum

    try:
        # 解析投票类型
        vote_enum = None
        if vote_type:
            vote_enum = VoteEnum(vote_type)

        # 获取投票数据
        votes = vote_service.get_votes_with_messages(
            page=page,
            size=size,
            vote_type=vote_enum,
            start_date=start_date,
            end_date=end_date,
            search_keyword=searchKeyword,
            client_type=client_type
        )

        # 获取总数
        total = vote_service.get_votes_with_messages_count(
            vote_type=vote_enum,
            start_date=start_date,
            end_date=end_date,
            search_keyword=searchKeyword,
            client_type=client_type
        )

        # 构建分页响应
        page_response = PageResponse(
            items=votes,
            total=total,
            page=page,
            size=size,
            has_next=page * size < total,
            has_prev=page > 1
        )

        return BaseResponse(data=page_response)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{vote_id}", response_model=BaseResponse[VoteRead])
async def get_vote(
    vote_id: int,
    vote_service: VoteService = Depends(get_vote_service),
    current_user: UserReadWithRole = Depends(require_any_role)
):
    """根据ID获取投票"""
    vote = vote_service.get_vote_by_id(vote_id)
    if not vote:
        raise HTTPException(status_code=404, detail="Vote not found")
    return BaseResponse(data=vote)


@router.get("/message/{message_id}", response_model=BaseResponse[List[VoteRead]])
async def get_votes_by_message(
    message_id: int,
    vote_service: VoteService = Depends(get_vote_service),
    current_user: UserReadWithRole = Depends(require_any_role)
):
    """获取指定消息的所有投票"""
    votes = vote_service.get_votes_by_message(message_id)
    return BaseResponse(data=votes)


@router.get("/", response_model=BaseResponse[PageResponse])
async def get_all_votes(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(10, ge=1, le=100, description="每页数量"),
    vote_service: VoteService = Depends(get_vote_service),
    current_user: UserReadWithRole = Depends(require_any_role)
):
    """分页获取所有投票"""
    votes = vote_service.get_all_votes(page=page, size=size)
    total = vote_service.get_total_votes_count()

    page_response = PageResponse(
        items=votes,
        total=total,
        page=page,
        size=size,
        has_next=page * size < total,
        has_prev=page > 1
    )
    return BaseResponse(data=page_response)


@router.put("/{vote_id}", response_model=BaseResponse[VoteRead])
async def update_vote(
    vote_id: int,
    vote_data: VoteUpdate,
    vote_service: VoteService = Depends(get_vote_service),
    current_user: UserReadWithRole = Depends(require_any_role)
):
    """更新投票"""
    try:
        vote = vote_service.update_vote(vote_id, vote_data)
        return BaseResponse(data=vote)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{vote_id}", response_model=BaseResponse[bool])
async def delete_vote(
    vote_id: int,
    vote_service: VoteService = Depends(get_vote_service),
    current_user: UserReadWithRole = Depends(require_any_role)
):
    """删除投票"""
    try:
        result = vote_service.delete_vote(vote_id)
        return BaseResponse(data=result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/stats/message/{message_id}", response_model=BaseResponse[VoteStats])
async def get_vote_stats_by_message(
    message_id: int,
    vote_service: VoteService = Depends(get_vote_service),
    current_user: UserReadWithRole = Depends(require_any_role)
):
    """获取指定消息的投票统计"""
    stats = vote_service.get_vote_stats_by_message(message_id)
    if not stats:
        # 如果没有投票记录，返回空的统计数据
        stats = VoteStats(
            message_id=message_id,
            good_count=0,
            average_count=0,
            poor_count=0,
            total_count=0
        )
    return BaseResponse(data=stats)


@router.get("/stats/type/{vote_type}", response_model=BaseResponse[int])
async def get_vote_stats_by_type(
    vote_type: str,
    vote_service: VoteService = Depends(get_vote_service),
    current_user: UserReadWithRole = Depends(require_any_role)
):
    """获取投票类型的统计数量"""
    from app.model.vote import VoteEnum

    try:
        vote_enum = VoteEnum(vote_type)
        count = vote_service.get_vote_stats_by_type(vote_enum)
        return BaseResponse(data=count)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid vote type: {vote_type}")


@router.get("/stats/overview", response_model=BaseResponse[dict])
async def get_vote_overview(
    vote_service: VoteService = Depends(get_vote_service),
    current_user: UserReadWithRole = Depends(require_any_role)
):
    """获取投票总体统计"""
    from app.model.vote import VoteEnum

    stats = {
        "total_votes": vote_service.get_total_votes_count(),
        "good_votes": vote_service.get_vote_stats_by_type(VoteEnum.good),
        "average_votes": vote_service.get_vote_stats_by_type(VoteEnum.medium),
        "poor_votes": vote_service.get_vote_stats_by_type(VoteEnum.bad)
    }
    return BaseResponse(data=stats)


@router.get("/user/message/{message_id}", response_model=BaseResponse[Optional[VoteRead]])
async def get_user_vote_for_message(
    message_id: int,
    user_id: Optional[str] = Query(None, description="用户ID（可选）"),
    vote_service: VoteService = Depends(get_vote_service),
    current_user: UserReadWithRole = Depends(require_any_role)
):
    """获取用户对指定消息的投票"""
    vote = vote_service.get_user_vote_for_message(message_id, user_id)
    return BaseResponse(data=vote)


@router.get("/export/excel")
async def export_votes_to_excel(
    vote_type: Optional[str] = Query(None, description="投票类型过滤 (good/medium/bad)"),
    start_date: Optional[datetime] = Query(None, description="开始时间 (YYYY-MM-DD HH:MM:SS)"),
    end_date: Optional[datetime] = Query(None, description="结束时间 (YYYY-MM-DD HH:MM:SS)"),
    searchKeyword: Optional[str] = Query(None, description="搜索关键词（搜索问题和回答）"),
    client_type: Optional[str] = Query(None, description="请求来源过滤 (web/h5/miniprogram/mp/公积金/rexian)"),
    vote_service: VoteService = Depends(get_vote_service),
    current_user: UserReadWithRole = Depends(require_any_role)
):
    """
    导出投票数据到Excel

    - **vote_type**: 投票类型过滤 (good/medium/bad)
    - **start_date**: 开始时间过滤
    - **end_date**: 结束时间过滤
    - **searchKeyword**: 搜索关键词（搜索问题和回答）
    - **client_type**: 请求来源过滤 (web/h5/miniprogram/mp/公积金/rexian)
    """
    from app.model.vote import VoteEnum

    try:
        # 解析投票类型
        vote_enum = None
        if vote_type:
            vote_enum = VoteEnum(vote_type)

        # 生成Excel文件
        excel_file = vote_service.export_votes_to_excel(
            vote_type=vote_enum,
            start_date=start_date,
            end_date=end_date,
            search_keyword=searchKeyword,
            client_type=client_type
        )

        # 生成文件名（使用ASCII文件名避免编码问题）
        from datetime import datetime as dt
        from urllib.parse import quote
        filename_ascii = f"vote_data_{dt.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filename_utf8 = f"问答数据_{dt.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        return StreamingResponse(
            excel_file,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                # 使用RFC 5987编码支持中文文件名
                "Content-Disposition": f"attachment; filename={filename_ascii}; filename*=UTF-8''{quote(filename_utf8)}"
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {str(e)}")
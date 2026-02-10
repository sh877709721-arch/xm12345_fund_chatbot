"""可视化大屏API接口"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from app.config.database import get_db
from app.service.dashboard import DashboardService
from app.schema.dashboard import (
    KpiStats,
    TrendStats,
    TimeSlotStats,
    SourceStats,
    TopQuestionsStats,
    VoteTypeStats,
    DashboardResponse
)
import logging

logging.basicConfig(level=logging.INFO)
router = APIRouter(prefix='/dashboard')


@router.get("/kpi", response_model=KpiStats)
async def get_kpi_stats(
    start_date: Optional[str] = Query(None, description="开始日期，格式：YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期，格式：YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """
    获取核心KPI统计

    返回指标：
    - total_qa: 总问答数（用户消息数量）
    - avg_daily_qa: 平均每日问答数
    - total_votes: 总投票数
    - good_rate: 好评率（百分比）

    查询参数：
    - start_date: 开始日期（可选，默认最近7天）
    - end_date: 结束日期（可选，默认今天）

    示例：GET v1/admin/dashboard/kpi?start_date=2026-01-01&end_date=2026-01-07
    """
    service = DashboardService(db)

    # 转换日期字符串为datetime对象
    start_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
    end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
    if end_dt:
        # 设置结束时间为当天的23:59:59
        end_dt = end_dt.replace(hour=23, minute=59, second=59)

    return service.get_kpi_stats(start_dt, end_dt)


@router.get("/trend", response_model=TrendStats)
async def get_trend_stats(
    start_date: Optional[str] = Query(None, description="开始日期，格式：YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期，格式：YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """
    获取问答趋势统计（按日期聚合）

    返回每日问答数量的趋势数据，用于绘制折线图

    返回格式：
    - series: 趋势数据点列表，每个点包含日期（MM-DD）和数量

    查询参数：
    - start_date: 开始日期（可选，默认最近7天）
    - end_date: 结束日期（可选，默认今天）

    示例：GET v1/admin/dashboard/trend?start_date=2026-01-01&end_date=2026-01-07
    """
    service = DashboardService(db)

    # 转换日期字符串为datetime对象
    start_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
    end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
    if end_dt:
        end_dt = end_dt.replace(hour=23, minute=59, second=59)

    return service.get_trend_stats(start_dt, end_dt)


@router.get("/time-slot", response_model=TimeSlotStats)
async def get_time_slot_stats(
    start_date: Optional[str] = Query(None, description="开始日期，格式：YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期，格式：YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """
    获取问答时段分布统计

    返回四个时段的问答分布：
    - 00-06: 凌晨时段
    - 06-12: 上午时段
    - 12-18: 下午时段
    - 18-24: 晚上时段

    返回格式：
    - series: 时段数据点列表，每个点包含时段和数量

    查询参数：
    - start_date: 开始日期（可选，默认最近7天）
    - end_date: 结束日期（可选，默认今天）

    示例：GET v1/admin/dashboard/time-slot?start_date=2026-01-01&end_date=2026-01-07
    """
    service = DashboardService(db)

    # 转换日期字符串为datetime对象
    start_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
    end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
    if end_dt:
        end_dt = end_dt.replace(hour=23, minute=59, second=59)

    return service.get_time_slot_stats(start_dt, end_dt)


@router.get("/source", response_model=SourceStats)
async def get_source_stats(
    start_date: Optional[str] = Query(None, description="开始日期，格式：YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期，格式：YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """
    获取问答来源分布统计

    返回各来源的问答分布：
    - 网页
    - H5
    - 小程序
    - 公众号
    - 公积金
    - 热线
    - 未知

    返回格式：
    - distribution: 来源数据点列表，每个点包含来源名称和数量

    查询参数：
    - start_date: 开始日期（可选，默认最近7天）
    - end_date: 结束日期（可选，默认今天）

    示例：GET v1/admin/dashboard/source?start_date=2026-01-01&end_date=2026-01-07
    """
    service = DashboardService(db)

    # 转换日期字符串为datetime对象
    start_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
    end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
    if end_dt:
        end_dt = end_dt.replace(hour=23, minute=59, second=59)

    return service.get_source_stats(start_dt, end_dt)


@router.get("/top-questions", response_model=TopQuestionsStats)
async def get_top_questions(
    start_date: Optional[str] = Query(None, description="开始日期，格式：YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期，格式：YYYY-MM-DD"),
    limit: int = Query(5, ge=1, le=20, description="返回数量（默认5，最大20）"),
    db: Session = Depends(get_db)
):
    """
    获取高频问答TOP5

    返回出现次数最高的问题列表

    返回格式：
    - questions: 问题列表，每个问题包含内容（question）和出现次数（count）

    查询参数：
    - start_date: 开始日期（可选，默认最近7天）
    - end_date: 结束日期（可选，默认今天）
    - limit: 返回数量（默认5，最大20）

    示例：GET v1/admin/dashboard/top-questions?start_date=2026-01-01&end_date=2026-01-07&limit=5
    """
    service = DashboardService(db)

    # 转换日期字符串为datetime对象
    start_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
    end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
    if end_dt:
        end_dt = end_dt.replace(hour=23, minute=59, second=59)

    return service.get_top_questions(start_dt, end_dt, limit)


@router.get("/vote-stats", response_model=VoteTypeStats)
async def get_vote_type_stats(
    start_date: Optional[str] = Query(None, description="开始日期，格式：YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期，格式：YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """
    获取投票类型统计

    返回各类型投票的数量：
    - good_count: 好评数
    - medium_count: 中评数
    - bad_count: 差评数
    - total_count: 总投票数

    查询参数：
    - start_date: 开始日期（可选，默认最近7天）
    - end_date: 结束日期（可选，默认今天）

    示例：GET v1/admin/dashboard/vote-stats?start_date=2026-01-01&end_date=2026-01-07
    """
    service = DashboardService(db)

    # 转换日期字符串为datetime对象
    start_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
    end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
    if end_dt:
        end_dt = end_dt.replace(hour=23, minute=59, second=59)

    return service.get_vote_type_stats(start_dt, end_dt)


@router.get("/full", response_model=DashboardResponse)
async def get_full_dashboard(
    start_date: Optional[str] = Query(None, description="开始日期，格式：YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期，格式：YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """
    获取完整的大屏数据（一次调用返回所有统计数据）

    返回所有可视化大屏需要的统计数据，适合前端一次性加载

    返回数据包括：
    - kpi: 核心KPI统计
    - trend: 问答趋势统计
    - time_slot: 时段分布统计
    - source: 来源分布统计
    - top_questions: 高频问答TOP5
    - vote_stats: 投票类型统计

    查询参数：
    - start_date: 开始日期（可选，默认最近7天）
    - end_date: 结束日期（可选，默认今天）

    示例：GET v1/admin/dashboard/full?start_date=2026-01-01&end_date=2026-01-07
    """
    service = DashboardService(db)

    # 转换日期字符串为datetime对象
    start_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
    end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
    if end_dt:
        end_dt = end_dt.replace(hour=23, minute=59, second=59)

    return service.get_full_dashboard(start_dt, end_dt)

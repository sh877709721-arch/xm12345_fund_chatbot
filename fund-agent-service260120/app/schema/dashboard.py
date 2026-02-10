"""可视化大屏数据模型"""
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


# ================== KPI数据模型 ==================
class KpiStats(BaseModel):
    """核心KPI统计"""
    total_qa: int  # 总问答数
    avg_daily_qa: int  # 平均每日问答数
    total_votes: int  # 总投票数
    good_rate: float  # 好评率


# ================== 趋势数据模型 ==================
class TrendDataPoint(BaseModel):
    """趋势数据点"""
    date: str  # 日期（格式：MM-DD）
    value: int  # 数值


class TrendStats(BaseModel):
    """问答趋势统计"""
    series: List[TrendDataPoint]  # 趋势数据序列


# ================== 时段分布数据模型 ==================
class TimeSlotDataPoint(BaseModel):
    """时段数据点"""
    time: str  # 时段（00-06, 06-12, 12-18, 18-24）
    value: int  # 数值


class TimeSlotStats(BaseModel):
    """问答时段分布统计"""
    series: List[TimeSlotDataPoint]  # 时段数据序列


# ================== 来源分布数据模型 ==================
class SourceDataPoint(BaseModel):
    """来源数据点"""
    name: str  # 来源名称（网页、H5、小程序、公众号、公积金、热线等）
    value: int  # 数量


class SourceStats(BaseModel):
    """问答来源分布统计"""
    distribution: List[SourceDataPoint]  # 来源分布数据


# ================== 高频问答数据模型 ==================
class TopQuestion(BaseModel):
    """高频问题"""
    question: str  # 问题内容
    count: int  # 出现次数


class TopQuestionsStats(BaseModel):
    """高频问答TOP5统计"""
    questions: List[TopQuestion]  # 高频问题列表


# ================== 投票统计数据模型 ==================
class VoteTypeStats(BaseModel):
    """投票类型统计"""
    good_count: int  # 好评数
    medium_count: int  # 中评数
    bad_count: int  # 差评数
    total_count: int  # 总投票数


# ================== 完整大屏数据模型 ==================
class DashboardResponse(BaseModel):
    """可视化大屏完整响应"""
    kpi: KpiStats  # KPI统计
    trend: TrendStats  # 趋势统计
    time_slot: TimeSlotStats  # 时段分布统计
    source: SourceStats  # 来源分布统计
    top_questions: TopQuestionsStats  # 高频问答统计
    vote_stats: VoteTypeStats  # 投票类型统计

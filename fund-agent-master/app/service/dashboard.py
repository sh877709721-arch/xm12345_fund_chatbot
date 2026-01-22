"""可视化大屏服务类"""
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import func, text, case, cast, Date
from sqlalchemy.orm import Session
from app.model.message import Message, MessageRoleEnum
from app.model.vote import Vote, VoteEnum
from app.schema.dashboard import (
    KpiStats,
    TrendStats,
    TrendDataPoint,
    TimeSlotStats,
    TimeSlotDataPoint,
    SourceStats,
    SourceDataPoint,
    TopQuestionsStats,
    TopQuestion,
    VoteTypeStats
)
from app.config.database import global_schema


class DashboardService:
    """可视化大屏服务类"""

    def __init__(self, db: Session):
        self.db = db

    def get_kpi_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> KpiStats:
        """
        获取核心KPI统计

        Args:
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            KpiStats: 包含总问答数、平均每日问答数、总投票数、好评率
        """
        # 如果没有指定日期范围，默认使用最近7天
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=6)  # 包含今天在内的7天

        # 计算日期差，用于计算平均值
        days_diff = (end_date - start_date).days + 1  # +1 包含当天

        # 获取总问答数（统计用户消息数量）
        total_qa_query = self.db.query(func.count(Message.id)).filter(
            Message.role == MessageRoleEnum.user,
            Message.created_at >= start_date,
            Message.created_at <= end_date
        )
        total_qa = total_qa_query.scalar() or 0

        # 计算平均每日问答数
        avg_daily_qa = int(total_qa / days_diff) if days_diff > 0 else 0

        # 获取总投票数
        total_votes_query = self.db.query(func.count(Vote.vote_id)).join(
            Message, Vote.message_id == Message.id
        ).filter(
            Message.created_at >= start_date,
            Message.created_at <= end_date
        )
        total_votes = total_votes_query.scalar() or 0

        # 获取好评数
        good_votes_query = self.db.query(func.count(Vote.vote_id)).join(
            Message, Vote.message_id == Message.id
        ).filter(
            Vote.vote_type == VoteEnum.good,
            Message.created_at >= start_date,
            Message.created_at <= end_date
        )
        good_count = good_votes_query.scalar() or 0

        # 计算好评率
        good_rate = (good_count / total_votes * 100) if total_votes > 0 else 0.0

        return KpiStats(
            total_qa=total_qa,
            avg_daily_qa=avg_daily_qa,
            total_votes=total_votes,
            good_rate=round(good_rate, 2)
        )

    def get_trend_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> TrendStats:
        """
        获取问答趋势统计（按日期聚合）

        Args:
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            TrendStats: 包含每日问答数量的趋势数据
        """
        # 如果没有指定日期范围，默认使用最近7天
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=6)

        # 查询每日问答数量
        query = self.db.query(
            func.date(Message.created_at).label('date'),
            func.count(Message.id).label('count')
        ).filter(
            Message.role == MessageRoleEnum.user,
            Message.created_at >= start_date,
            Message.created_at <= end_date
        ).group_by(
            func.date(Message.created_at)
        ).order_by(
            func.date(Message.created_at)
        )

        results = query.all()

        # 生成完整日期序列（包含没有数据的日期）
        trend_series = []
        current_date = start_date.date()
        end_date_only = end_date.date()

        result_dict = {row.date: row.count for row in results}

        while current_date <= end_date_only:
            count = result_dict.get(current_date, 0)
            # 格式化日期为 MM-DD
            date_str = current_date.strftime("%m-%d")
            trend_series.append(TrendDataPoint(date=date_str, value=count))
            current_date += timedelta(days=1)

        return TrendStats(series=trend_series)

    def get_time_slot_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> TimeSlotStats:
        """
        获取问答时段分布统计

        Args:
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            TimeSlotStats: 包含四个时段（00-06, 06-12, 12-18, 18-24）的问答分布
        """
        # 如果没有指定日期范围，默认使用最近7天
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=6)

        # 查询时段分布
        # 使用CASE语句将小时分组到四个时段
        query = self.db.query(
            case(
                (func.extract('hour', Message.created_at) < 6, '00-06'),
                (func.extract('hour', Message.created_at) < 12, '06-12'),
                (func.extract('hour', Message.created_at) < 18, '12-18'),
                else_='18-24'
            ).label('time_slot'),
            func.count(Message.id).label('count')
        ).filter(
            Message.role == MessageRoleEnum.user,
            Message.created_at >= start_date,
            Message.created_at <= end_date
        ).group_by('time_slot').order_by('time_slot')

        results = query.all()

        # 构建结果字典，确保所有时段都存在
        result_dict = {row.time_slot: row.count for row in results}

        # 按照固定顺序返回
        time_slots = ['00-06', '06-12', '12-18', '18-24']
        series = [
            TimeSlotDataPoint(time=slot, value=result_dict.get(slot, 0))
            for slot in time_slots
        ]

        return TimeSlotStats(series=series)

    def get_source_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> SourceStats:
        """
        获取问答来源分布统计

        Args:
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            SourceStats: 包含各来源（网页、H5、小程序、公众号、公积金、热线等）的问答分布
        """
        # 如果没有指定日期范围，默认使用最近7天
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=6)

        # 使用原生SQL查询来源分布（从metadata_字段提取client信息）
        query = text(f"""
            SELECT
                CASE
                    WHEN metadata_->>'client' = 'web' THEN '网页'
                    WHEN metadata_->>'client' = 'h5' THEN 'H5'
                    WHEN metadata_->>'client' = 'miniprogram' THEN '小程序'
                    WHEN metadata_->>'client' = 'mp' THEN '公众号'
                    WHEN metadata_->>'client' = '公积金' THEN '公积金'
                    WHEN metadata_->>'client' = 'rexian' THEN '热线'
                    WHEN metadata_->>'client' IS NOT NULL THEN metadata_->>'client'
                    ELSE '未知'
                END as client_type,
                COUNT(*) as count
            FROM {global_schema}.messages
            WHERE message_role_enum = 'user'
                AND created_at >= :start_date
                AND created_at <= :end_date
            GROUP BY client_type
            ORDER BY count DESC
        """)

        result = self.db.execute(query, {
            "start_date": start_date,
            "end_date": end_date
        })
        rows = result.fetchall()

        distribution = [
            SourceDataPoint(name=row.client_type, value=row.count)
            for row in rows
        ]

        return SourceStats(distribution=distribution)

    def get_top_questions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 5
    ) -> TopQuestionsStats:
        """
        获取高频问答TOP5

        Args:
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            limit: 返回数量（默认5）

        Returns:
            TopQuestionsStats: 包含出现次数最高的问题列表
        """
        # 如果没有指定日期范围，默认使用最近7天
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=6)

        # 查询高频问题
        query = self.db.query(
            Message.content.label('question'),
            func.count(Message.id).label('count')
        ).filter(
            Message.role == MessageRoleEnum.user,
            Message.created_at >= start_date,
            Message.created_at <= end_date,
            Message.content.isnot(None),
            Message.content != ''
        ).group_by(
            Message.content
        ).order_by(
            func.count(Message.id).desc()
        ).limit(limit)

        results = query.all()

        questions = [
            TopQuestion(question=row.question, count=row.count)
            for row in results
        ]

        return TopQuestionsStats(questions=questions)

    def get_vote_type_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> VoteTypeStats:
        """
        获取投票类型统计

        Args:
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            VoteTypeStats: 包含好评、中评、差评的数量和总数
        """
        # 如果没有指定日期范围，默认使用最近7天
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=6)

        # 获取投票统计
        stats_query = self.db.query(
            func.sum(case((Vote.vote_type == VoteEnum.good, 1), else_=0)).label('good_count'),
            func.sum(case((Vote.vote_type == VoteEnum.medium, 1), else_=0)).label('medium_count'),
            func.sum(case((Vote.vote_type == VoteEnum.bad, 1), else_=0)).label('bad_count'),
            func.count(Vote.vote_id).label('total_count')
        ).join(
            Message, Vote.message_id == Message.id
        ).filter(
            Message.created_at >= start_date,
            Message.created_at <= end_date
        ).first()

        return VoteTypeStats(
            good_count=int(stats_query.good_count or 0),
            medium_count=int(stats_query.medium_count or 0),
            bad_count=int(stats_query.bad_count or 0),
            total_count=int(stats_query.total_count or 0)
        )

    def get_full_dashboard(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> dict:
        """
        获取完整的大屏数据（一次调用返回所有统计数据）

        Args:
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）

        Returns:
            dict: 包含所有大屏统计数据的字典
        """
        return {
            "kpi": self.get_kpi_stats(start_date, end_date),
            "trend": self.get_trend_stats(start_date, end_date),
            "time_slot": self.get_time_slot_stats(start_date, end_date),
            "source": self.get_source_stats(start_date, end_date),
            "top_questions": self.get_top_questions(start_date, end_date),
            "vote_stats": self.get_vote_type_stats(start_date, end_date)
        }

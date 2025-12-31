from typing import List, Optional
from datetime import datetime
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.model.vote import Vote, VoteEnum
from app.schema.vote import VoteCreate, VoteRead, VoteStats, VoteUpdate, VoteWithMessage


class VoteService:
    def __init__(self, db: Session):
        self.db = db

    def create_vote(self, vote_data: VoteCreate) -> VoteRead:
        """创建新的投票"""
        try:
            # 检查该消息是否已经被投票过（可选业务逻辑）
            existing_vote_db = self.db.query(Vote).filter(
                Vote.message_id == vote_data.message_id
            ).first()

            if existing_vote_db:
                # 如果存在，更新现有投票
                existing_vote_db.set_vote_type(vote_data.vote_type)
                if vote_data.feedback is not None:
                    existing_vote_db.set_feedback_content(feedback_content=vote_data.feedback)
                else:
                    existing_vote_db.set_feedback_content(feedback_content="")
                self.db.commit()
                self.db.refresh(existing_vote_db)
                return VoteRead.model_validate(existing_vote_db)

            # 创建新投票
            vote = Vote(
                message_id=vote_data.message_id,
                vote_type=vote_data.vote_type.value,
                feedback = vote_data.feedback                
            )

            self.db.add(vote)
            self.db.commit()
            self.db.refresh(vote)

            return VoteRead.model_validate(vote)
        except Exception as e:
            self.db.rollback()
            raise e

    def get_vote_by_id(self, vote_id: int) -> Optional[VoteRead]:
        """根据ID获取投票"""
        vote = self.db.query(Vote).filter(Vote.vote_id == vote_id).first()
        if vote:
            return VoteRead.model_validate(vote)
        return None

    def get_votes_by_message(self, message_id: int) -> List[VoteRead]:
        """获取某个消息的所有投票"""
        votes = self.db.query(Vote).filter(Vote.message_id == message_id).all()
        return [VoteRead.model_validate(vote) for vote in votes]

    def get_all_votes(self, page: int = 1, size: int = 10) -> List[VoteRead]:
        """分页获取所有投票"""
        offset = (page - 1) * size
        votes = self.db.query(Vote).offset(offset).limit(size).all()
        return [VoteRead.model_validate(vote) for vote in votes]

    def get_total_votes_count(self) -> int:
        """获取总投票数"""
        return self.db.query(Vote).count()

    def update_vote(self, vote_id: int, vote_data: VoteUpdate) -> VoteRead:
        """更新投票"""
        try:
            vote = self.db.query(Vote).filter(Vote.vote_id == vote_id).first()
            if not vote:
                raise ValueError(f"Vote with ID {vote_id} not found")
            vote.vote_type = vote_data.vote_type.value
            self.db.commit()
            self.db.refresh(vote)

            return VoteRead.model_validate(vote)
        except Exception as e:
            self.db.rollback()
            raise e

    def delete_vote(self, vote_id: int) -> bool:
        """删除投票"""
        try:
            vote = self.db.query(Vote).filter(Vote.vote_id == vote_id).first()
            if not vote:
                raise ValueError(f"Vote with ID {vote_id} not found")

            self.db.delete(vote)
            self.db.commit()

            return True
        except Exception as e:
            self.db.rollback()
            raise e

    def get_vote_stats_by_message(self, message_id: int) -> Optional[VoteStats]:
        """获取某个消息的投票统计"""
        from sqlalchemy import case

        # 构建统计查询
        stats_query = (
            self.db.query(
                Vote.message_id,
                func.sum(case((Vote.vote_type == VoteEnum.good, 1), else_=0)).label('good_count'),
                func.sum(case((Vote.vote_type == VoteEnum.medium, 1), else_=0)).label('average_count'),
                func.sum(case((Vote.vote_type == VoteEnum.bad, 1), else_=0)).label('poor_count'),
                func.count(Vote.vote_id).label('total_count')
            )
            .filter(Vote.message_id == message_id)
            .group_by(Vote.message_id)
            .first()
        )

        if stats_query:
            return VoteStats(
                message_id=stats_query.message_id,
                good_count=int(stats_query.good_count or 0),
                average_count=int(stats_query.average_count or 0),
                poor_count=int(stats_query.poor_count or 0),
                total_count=int(stats_query.total_count or 0)
            )
        return None

    def get_vote_stats_by_type(self, vote_type: VoteEnum) -> int:
        """获取某种投票类型的总数"""
        return self.db.query(Vote).filter(Vote.vote_type == vote_type).count()

    def get_user_vote_for_message(self, message_id: int, user_id: Optional[str] = None) -> Optional[VoteRead]:
        """获取用户对特定消息的投票（如果需要用户关联的话）"""
        # 注意：当前的 Vote 模型没有 user_id 字段，这里作为扩展接口
        # 如果需要用户关联，需要修改模型
        vote = self.db.query(Vote).filter(Vote.message_id == message_id).first()
        if vote:
            return VoteRead.model_validate(vote)
        return None

    def get_votes_with_messages(
        self,
        page: int = 1,
        size: int = 10,
        vote_type: Optional[VoteEnum] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[VoteWithMessage]:
        """获取带问题和答案的投票列表（支持按类型和时间过滤）"""
        offset = (page - 1) * size

        # 构建基础查询
        base_query_old = """
            SELECT
                a.vote_id,
                a.message_id,
                a.vote_type,
                a.feedback,
                a.updated_at,
                user_latest.content as question,
                b.content as answer,
                b.chat_id
            FROM chatbot.vote a
            LEFT JOIN chatbot.messages b ON a.message_id = b.id
            LEFT JOIN LATERAL (
                SELECT *
                FROM chatbot.messages
                WHERE chat_id = b.chat_id
                AND message_role_enum = 'user'
                AND id < b.id
                ORDER BY created_at DESC
                LIMIT 1
            ) user_latest ON true
            WHERE 1=1
        """

        base_query = """
            select 
                a.id as message_id,
                a.chat_id,
                a.content as question,
                user_latest.content as answer,
                a.created_at as created_at,
                coalesce(c.vote_type,'unknown') vote_type,
                c.vote_id,
                c.feedback feedback,
                c.updated_at updated_at
            from chatbot.messages a
            left join lateral (
                select id,chat_id,message_role_enum,content,created_at 
                from chatbot.messages 
                where chat_id = a.chat_id
                and message_role_enum = 'assistant'
                and id < a.id
                order by created_at desc limit 1
            ) user_latest ON true
            left join chatbot.vote c on user_latest.id = c.message_id 
            where a.message_role_enum = 'user'
        """
        # 构建条件参数
        conditions = []
        params = {"limit": size, "offset": offset}

        if vote_type:
            conditions.append("AND a.vote_type = :vote_type")
            params["vote_type"] = vote_type.value

        if start_date:
            conditions.append("AND a.created_at >= :start_date")
            params["start_date"] = start_date

        if end_date:
            conditions.append("AND a.created_at <= :end_date")
            params["end_date"] = end_date

        # 组装完整查询
        full_query = base_query + " ".join(conditions) + " ORDER BY a.created_at DESC LIMIT :limit OFFSET :offset"

        result = self.db.execute(text(full_query), params)
        rows = result.fetchall()

        return [VoteWithMessage(
            vote_id=row.vote_id,
            message_id=row.message_id,
            vote_type=row.vote_type,
            feedback=row.feedback,
            created_at=row.created_at,
            question=row.question,
            answer=row.answer,
            chat_id=row.chat_id
        ) for row in rows]

    def get_votes_with_messages_count(
        self,
        vote_type: Optional[VoteEnum] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """获取带问题和答案的投票总数（用于分页）"""

        # 构建基础查询
        base_query = """
            SELECT COUNT(DISTINCT a.vote_id) as total
            FROM chatbot.vote a
            LEFT JOIN chatbot.messages b ON a.message_id = b.id
            LEFT JOIN LATERAL (
                SELECT *
                FROM chatbot.messages
                WHERE chat_id = b.chat_id
                AND message_role_enum = 'user'
                AND id < b.id
                ORDER BY created_at DESC
                LIMIT 1
            ) user_latest ON true
            WHERE 1=1
        """

        # 构建条件参数
        conditions = []
        params = {}

        if vote_type:
            conditions.append("AND a.vote_type = :vote_type")
            params["vote_type"] = vote_type.value

        if start_date:
            conditions.append("AND a.updated_at >= :start_date")
            params["start_date"] = start_date

        if end_date:
            conditions.append("AND a.updated_at <= :end_date")
            params["end_date"] = end_date

        # 组装完整查询
        full_query = base_query + " ".join(conditions)

        result = self.db.execute(text(full_query), params)
        row = result.fetchone()

        return int(row.total) if row else 0

    def get_votes_with_messages_by_chat(self, chat_id: str) -> List[VoteWithMessage]:
        """根据聊天ID获取带问题和答案的投票列表"""
        query = text("""
            SELECT
                a.vote_id,
                a.message_id,
                a.vote_type,
                a.updated_at,
                user_latest.content as question,
                b.content as answer,
                b.chat_id
            FROM chatbot.vote a
            LEFT JOIN chatbot.messages b ON a.message_id = b.id
            LEFT JOIN LATERAL (
                SELECT *
                FROM chatbot.messages
                WHERE chat_id = b.chat_id
                AND message_role_enum = 'user'
                AND id < b.id     
                ORDER BY created_at DESC
                LIMIT 1
            ) user_latest ON true
            WHERE b.chat_id = :chat_id
            ORDER BY a.updated_at DESC
        """)

        result = self.db.execute(query, {"chat_id": chat_id})
        rows = result.fetchall()

        return [VoteWithMessage(
            vote_id=row.vote_id,
            message_id=row.message_id,
            vote_type=row.vote_type,
            updated_at=row.updated_at,
            question=row.question,
            answer=row.answer,
            chat_id=row.chat_id
        ) for row in rows]
    
    
"""Audit service."""
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.clickhouse import (
    get_risk_events,
    insert_audit_log,
    query_audit_logs,
)


class AuditService:
    """Audit business service."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def query_logs(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        user_id: Optional[int] = None,
        model_name: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> dict:
        """Query audit logs."""
        logs, total = query_audit_logs(
            start_time=start_time,
            end_time=end_time,
            user_id=user_id,
            model_name=model_name,
            page=page,
            page_size=page_size
        )
        
        return {
            "data": logs,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    
    async def get_risk_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        risk_level: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[list[dict], int]:
        """Get risk events."""
        if not start_time:
            start_time = datetime.utcnow() - timedelta(days=7)
        if not end_time:
            end_time = datetime.utcnow()
        
        return get_risk_events(
            start_time=start_time,
            end_time=end_time,
            risk_level=risk_level,
            page=page,
            page_size=page_size
        )
    
    async def get_user_statistics(
        self,
        user_id: int,
        start_date: str,
        end_date: str
    ) -> list[dict]:
        """Get user usage statistics."""
        # Query from ClickHouse
        from app.db.clickhouse import get_clickhouse
        
        client = get_clickhouse()
        
        result = client.execute(
            """
            SELECT 
                toDate(timestamp) as date,
                count() as total_requests,
                sum(total_tokens) as total_tokens,
                sum(prompt_tokens) as prompt_tokens,
                sum(completion_tokens) as completion_tokens
            FROM audit_logs
            WHERE user_id = %(user_id)s
              AND toDate(timestamp) >= %(start_date)s
              AND toDate(timestamp) <= %(end_date)s
            GROUP BY date
            ORDER BY date
            """,
            {
                "user_id": user_id,
                "start_date": start_date,
                "end_date": end_date,
            }
        )
        
        stats = []
        for row in result:
            stats.append({
                "date": row[0].strftime("%Y-%m-%d"),
                "total_requests": row[1],
                "total_tokens": row[2],
                "prompt_tokens": row[3],
                "completion_tokens": row[4],
            })
        
        return stats
    
    async def get_dashboard_stats(self) -> dict:
        """Get dashboard statistics."""
        from app.db.clickhouse import get_clickhouse
        
        client = get_clickhouse()
        stats = {}
        
        # Today's requests
        result = client.execute(
            "SELECT count() FROM audit_logs WHERE toDate(timestamp) = today()"
        )
        stats["today_requests"] = result[0][0] if result else 0
        
        # Today's tokens
        result = client.execute(
            "SELECT sum(total_tokens) FROM audit_logs WHERE toDate(timestamp) = today()"
        )
        stats["today_tokens"] = result[0][0] if result else 0
        
        # Active users today
        result = client.execute(
            "SELECT uniqExact(user_id) FROM audit_logs WHERE toDate(timestamp) = today()"
        )
        stats["active_users"] = result[0][0] if result else 0
        
        # Risk events today
        result = client.execute(
            "SELECT count() FROM risk_events WHERE toDate(timestamp) = today()"
        )
        stats["risk_events"] = result[0][0] if result else 0
        
        # 7-day trends
        result = client.execute(
            """
            SELECT 
                toDate(timestamp) as date,
                count() as requests,
                sum(total_tokens) as tokens
            FROM audit_logs
            WHERE timestamp >= now() - INTERVAL 7 DAY
            GROUP BY date
            ORDER BY date
            """
        )
        trends = []
        for row in result:
            trends.append({
                "date": row[0].strftime("%Y-%m-%d"),
                "requests": row[1],
                "tokens": row[2],
            })
        stats["trends"] = trends
        
        # Model usage today
        result = client.execute(
            """
            SELECT 
                model_name,
                count() as requests,
                sum(total_tokens) as tokens
            FROM audit_logs
            WHERE toDate(timestamp) = today()
            GROUP BY model_name
            ORDER BY requests DESC
            LIMIT 10
            """
        )
        model_stats = []
        for row in result:
            model_stats.append({
                "model_name": row[0],
                "requests": row[1],
                "tokens": row[2],
            })
        stats["model_stats"] = model_stats
        
        return stats
    
    async def resolve_risk_event(
        self,
        event_id: str,
        resolved_by: str,
        note: str = ""
    ) -> bool:
        """Resolve a risk event."""
        from app.db.clickhouse import get_clickhouse
        
        client = get_clickhouse()
        client.execute(
            """
            ALTER TABLE risk_events
            UPDATE is_resolved = 1, resolved_by = %(resolved_by)s, 
                   resolved_at = now(), note = %(note)s
            WHERE event_id = %(event_id)s
            """,
            {
                "event_id": event_id,
                "resolved_by": resolved_by,
                "note": note,
            }
        )
        return True

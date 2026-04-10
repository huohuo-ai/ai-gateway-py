"""ClickHouse database connection."""
from datetime import datetime
from typing import Any, Optional

from clickhouse_driver import Client as SyncClient
from clickhouse_driver import connect

from app.config import settings

# ClickHouse client instance
_clickhouse_client: Optional[SyncClient] = None


def get_clickhouse() -> SyncClient:
    """Get ClickHouse client (synchronous)."""
    global _clickhouse_client
    if _clickhouse_client is None:
        _clickhouse_client = connect(
            host=settings.clickhouse.host,
            port=settings.clickhouse.port,
            database=settings.clickhouse.database,
            user=settings.clickhouse.username,
            password=settings.clickhouse.password or "",
        )
    return _clickhouse_client


def close_clickhouse() -> None:
    """Close ClickHouse connection."""
    global _clickhouse_client
    if _clickhouse_client:
        _clickhouse_client.disconnect()
        _clickhouse_client = None


def init_clickhouse_tables() -> None:
    """Initialize ClickHouse tables."""
    client = get_clickhouse()
    
    # Create audit_logs table
    client.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            timestamp DateTime64(3),
            request_id UUID,
            user_id UInt64,
            user_name String,
            user_email String,
            request_time DateTime64(3),
            request_method String,
            request_path String,
            request_ip String,
            user_agent String,
            request_headers String,
            request_body String,
            model_name String,
            model_provider String,
            response_time DateTime64(3),
            response_status UInt16,
            response_body String,
            response_headers String,
            prompt_tokens Int64,
            completion_tokens Int64,
            total_tokens Int64,
            latency_ms Int64,
            is_stream Bool,
            has_error Bool,
            error_message String
        ) ENGINE = MergeTree()
        ORDER BY (timestamp, user_id)
        TTL timestamp + INTERVAL 90 DAY
        SETTINGS index_granularity = 8192
    """)
    
    # Create risk_events table
    client.execute("""
        CREATE TABLE IF NOT EXISTS risk_events (
            timestamp DateTime64(3),
            event_id UUID,
            request_id UUID,
            user_id UInt64,
            user_name String,
            risk_level String,
            risk_type String,
            risk_score Float64,
            risk_reason String,
            description String,
            evidence String,
            request_ip String,
            model_name String,
            is_resolved Bool DEFAULT False,
            resolved_by String DEFAULT '',
            resolved_at DateTime64(3) DEFAULT '1970-01-01 00:00:00',
            note String DEFAULT ''
        ) ENGINE = MergeTree()
        ORDER BY (timestamp, risk_level)
        TTL timestamp + INTERVAL 180 DAY
        SETTINGS index_granularity = 8192
    """)


def insert_audit_log(log_data: dict[str, Any]) -> None:
    """Insert audit log into ClickHouse."""
    client = get_clickhouse()
    
    client.execute(
        """
        INSERT INTO audit_logs (
            timestamp, request_id, user_id, user_name, user_email,
            request_time, request_method, request_path, request_ip, user_agent,
            request_headers, request_body, model_name, model_provider,
            response_time, response_status, response_body, response_headers,
            prompt_tokens, completion_tokens, total_tokens, latency_ms,
            is_stream, has_error, error_message
        ) VALUES
        """,
        [(
            log_data.get("timestamp", datetime.utcnow()),
            log_data.get("request_id"),
            log_data.get("user_id", 0),
            log_data.get("user_name", ""),
            log_data.get("user_email", ""),
            log_data.get("request_time", datetime.utcnow()),
            log_data.get("request_method", ""),
            log_data.get("request_path", ""),
            log_data.get("request_ip", ""),
            log_data.get("user_agent", ""),
            log_data.get("request_headers", ""),
            log_data.get("request_body", "")[:10000],
            log_data.get("model_name", ""),
            log_data.get("model_provider", ""),
            log_data.get("response_time", datetime.utcnow()),
            log_data.get("response_status", 200),
            log_data.get("response_body", "")[:10000],
            log_data.get("response_headers", ""),
            log_data.get("prompt_tokens", 0),
            log_data.get("completion_tokens", 0),
            log_data.get("total_tokens", 0),
            log_data.get("latency_ms", 0),
            log_data.get("is_stream", False),
            log_data.get("has_error", False),
            log_data.get("error_message", ""),
        )]
    )


def insert_risk_event(event_data: dict[str, Any]) -> None:
    """Insert risk event into ClickHouse."""
    client = get_clickhouse()
    
    client.execute(
        """
        INSERT INTO risk_events (
            timestamp, event_id, request_id, user_id, user_name,
            risk_level, risk_type, risk_score, risk_reason, description,
            evidence, request_ip, model_name
        ) VALUES
        """,
        [(
            event_data.get("timestamp", datetime.utcnow()),
            event_data.get("event_id"),
            event_data.get("request_id"),
            event_data.get("user_id", 0),
            event_data.get("user_name", ""),
            event_data.get("risk_level", "low"),
            event_data.get("risk_type", ""),
            event_data.get("risk_score", 0.0),
            event_data.get("risk_reason", ""),
            event_data.get("description", ""),
            event_data.get("evidence", ""),
            event_data.get("request_ip", ""),
            event_data.get("model_name", ""),
        )]
    )


def query_audit_logs(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    user_id: Optional[int] = None,
    model_name: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> tuple[list[dict], int]:
    """Query audit logs."""
    client = get_clickhouse()
    
    where_clauses = ["1=1"]
    params = {}
    
    if start_time:
        where_clauses.append("timestamp >= %(start_time)s")
        params["start_time"] = start_time
    if end_time:
        where_clauses.append("timestamp <= %(end_time)s")
        params["end_time"] = end_time
    if user_id:
        where_clauses.append("user_id = %(user_id)s")
        params["user_id"] = user_id
    if model_name:
        where_clauses.append("model_name = %(model_name)s")
        params["model_name"] = model_name
    
    where_sql = " AND ".join(where_clauses)
    
    # Get total count
    count_result = client.execute(
        f"SELECT count() FROM audit_logs WHERE {where_sql}",
        params
    )
    total = count_result[0][0] if count_result else 0
    
    # Get paginated results
    offset = (page - 1) * page_size
    results = client.execute(
        f"""
        SELECT *
        FROM audit_logs
        WHERE {where_sql}
        ORDER BY timestamp DESC
        LIMIT %(page_size)s OFFSET %(offset)s
        """,
        {**params, "page_size": page_size, "offset": offset}
    )
    
    columns = [
        "timestamp", "request_id", "user_id", "user_name", "user_email",
        "request_time", "request_method", "request_path", "request_ip", "user_agent",
        "request_headers", "request_body", "model_name", "model_provider",
        "response_time", "response_status", "response_body", "response_headers",
        "prompt_tokens", "completion_tokens", "total_tokens", "latency_ms",
        "is_stream", "has_error", "error_message"
    ]
    
    logs = [dict(zip(columns, row)) for row in results]
    return logs, total


def get_risk_events(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    risk_level: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
) -> tuple[list[dict], int]:
    """Get risk events."""
    client = get_clickhouse()
    
    where_clauses = ["1=1"]
    params = {}
    
    if start_time:
        where_clauses.append("timestamp >= %(start_time)s")
        params["start_time"] = start_time
    if end_time:
        where_clauses.append("timestamp <= %(end_time)s")
        params["end_time"] = end_time
    if risk_level:
        where_clauses.append("risk_level = %(risk_level)s")
        params["risk_level"] = risk_level
    
    where_sql = " AND ".join(where_clauses)
    
    # Get total count
    count_result = client.execute(
        f"SELECT count() FROM risk_events WHERE {where_sql}",
        params
    )
    total = count_result[0][0] if count_result else 0
    
    # Get paginated results
    offset = (page - 1) * page_size
    results = client.execute(
        f"""
        SELECT *
        FROM risk_events
        WHERE {where_sql}
        ORDER BY timestamp DESC
        LIMIT %(page_size)s OFFSET %(offset)s
        """,
        {**params, "page_size": page_size, "offset": offset}
    )
    
    columns = [
        "timestamp", "event_id", "request_id", "user_id", "user_name",
        "risk_level", "risk_type", "risk_score", "risk_reason", "description",
        "evidence", "request_ip", "model_name", "is_resolved", "resolved_by",
        "resolved_at", "note"
    ]
    
    events = [dict(zip(columns, row)) for row in results]
    return events, total

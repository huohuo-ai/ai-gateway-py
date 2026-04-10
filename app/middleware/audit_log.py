"""Audit logging middleware."""
import json
from datetime import datetime

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.audit.detector import RiskDetector, detect_frequency_risk, process_audit_log
from app.config import settings
from app.core.constants import MAX_AUDIT_CONTENT_LENGTH, REQUEST_ID_HEADER
from app.core.security import generate_uuid
from app.db.clickhouse import insert_audit_log


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests to ClickHouse."""
    
    async def dispatch(self, request: Request, call_next):
        # Skip logging for certain paths
        path = request.url.path
        if path in ["/health", "/api/v1/auth/login", "/api/v1/auth/register"]:
            return await call_next(request)
        
        # Generate request ID
        request_id = generate_uuid()
        request.state.request_id = request_id
        
        # Record start time
        start_time = datetime.utcnow()
        
        # Read request body
        request_body = ""
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                request_body = body.decode("utf-8", errors="replace")[:MAX_AUDIT_CONTENT_LENGTH]
                # Restore body for next middleware
                async def receive():
                    return {"type": "http.request", "body": body}
                request._receive = receive
            except Exception:
                pass
        
        # Process request
        response = await call_next(request)
        
        # Calculate latency
        end_time = datetime.utcnow()
        latency_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Get user info from request state
        user_id = getattr(request.state, "user_id", 0)
        username = getattr(request.state, "username", "")
        user_email = getattr(request.state, "user_email", "")
        
        # Extract model name from request body
        model_name = ""
        try:
            body_json = json.loads(request_body)
            model_name = body_json.get("model", "")
        except (json.JSONDecodeError, AttributeError):
            pass
        
        # Read response body (if not streaming)
        response_body = ""
        is_stream = False
        
        # Build audit log
        audit_log = {
            "timestamp": end_time,
            "request_id": request_id,
            "user_id": user_id,
            "user_name": username,
            "user_email": user_email,
            "request_time": start_time,
            "request_method": request.method,
            "request_path": path,
            "request_ip": request.client.host if request.client else "",
            "user_agent": request.headers.get("user-agent", ""),
            "request_headers": json.dumps(dict(request.headers)),
            "request_body": request_body[:MAX_AUDIT_CONTENT_LENGTH],
            "model_name": model_name,
            "model_provider": "",
            "response_time": end_time,
            "response_status": response.status_code,
            "response_body": response_body[:MAX_AUDIT_CONTENT_LENGTH],
            "response_headers": json.dumps(dict(response.headers)),
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "latency_ms": latency_ms,
            "is_stream": is_stream,
            "has_error": response.status_code >= 400,
            "error_message": "",
        }
        
        # Try to extract token usage from response (for non-streaming)
        if not is_stream and response_body:
            try:
                resp_json = json.loads(response_body)
                if "usage" in resp_json:
                    usage = resp_json["usage"]
                    audit_log["prompt_tokens"] = usage.get("prompt_tokens", 0)
                    audit_log["completion_tokens"] = usage.get("completion_tokens", 0)
                    audit_log["total_tokens"] = usage.get("total_tokens", 0)
            except (json.JSONDecodeError, AttributeError):
                pass
        
        # Add request ID header to response
        response.headers[REQUEST_ID_HEADER] = request_id
        
        # Insert audit log asynchronously (fire and forget)
        try:
            insert_audit_log(audit_log)
        except Exception as e:
            import logging
            logging.error(f"Failed to insert audit log: {e}")
        
        # Risk detection
        try:
            process_audit_log(audit_log)
        except Exception as e:
            import logging
            logging.error(f"Risk detection failed: {e}")
        
        # Frequency check
        try:
            freq_risk = await detect_frequency_risk(
                user_id,
                request.client.host if request.client else ""
            )
            if freq_risk:
                from app.db.clickhouse import insert_risk_event
                insert_risk_event(freq_risk.to_dict())
        except Exception as e:
            import logging
            logging.error(f"Frequency check failed: {e}")
        
        return response

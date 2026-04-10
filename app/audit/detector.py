"""Risk detection engine."""
import json
import re
from datetime import datetime
from typing import Any, Optional

from app.config import settings
from app.core.constants import (
    DEFAULT_INJECTION_PATTERNS,
    DEFAULT_SENSITIVE_KEYWORDS,
    RiskLevel,
    RiskType,
)
from app.db.clickhouse import insert_risk_event
from app.db.redis import get_redis


class RiskEvent:
    """Risk event data class."""
    
    def __init__(
        self,
        event_id: str,
        request_id: str,
        user_id: int,
        user_name: str,
        risk_level: str,
        risk_type: str,
        risk_score: float,
        risk_reason: str,
        description: str,
        evidence: dict,
        request_ip: str,
        model_name: str
    ):
        self.timestamp = datetime.utcnow()
        self.event_id = event_id
        self.request_id = request_id
        self.user_id = user_id
        self.user_name = user_name
        self.risk_level = risk_level
        self.risk_type = risk_type
        self.risk_score = risk_score
        self.risk_reason = risk_reason
        self.description = description
        self.evidence = evidence
        self.request_ip = request_ip
        self.model_name = model_name
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp,
            "event_id": self.event_id,
            "request_id": self.request_id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "risk_level": self.risk_level,
            "risk_type": self.risk_type,
            "risk_score": self.risk_score,
            "risk_reason": self.risk_reason,
            "description": self.description,
            "evidence": json.dumps(self.evidence),
            "request_ip": self.request_ip,
            "model_name": self.model_name,
        }


class RiskDetector:
    """Risk detection engine."""
    
    def __init__(self):
        self.cfg = settings.audit
    
    def detect(self, audit_log: dict) -> Optional[RiskEvent]:
        """Detect risks in audit log."""
        events = []
        
        # 1. Token abuse detection
        if event := self._detect_token_abuse(audit_log):
            events.append(event)
        
        # 2. Off-hours access detection
        if event := self._detect_off_hours(audit_log):
            events.append(event)
        
        # 3. Sensitive info detection
        if event := self._detect_sensitive_info(audit_log):
            events.append(event)
        
        # 4. Abnormal frequency detection
        # Note: This is async, handled separately
        
        # 5. IP anomaly detection
        if event := self._detect_ip_anomaly(audit_log):
            events.append(event)
        
        # 6. Abnormal pattern detection
        if event := self._detect_abnormal_pattern(audit_log):
            events.append(event)
        
        if not events:
            return None
        
        if len(events) == 1:
            return events[0]
        
        # Merge multiple events
        return self._merge_events(audit_log, events)
    
    def _detect_token_abuse(self, audit_log: dict) -> Optional[RiskEvent]:
        """Detect token abuse."""
        total_tokens = audit_log.get("total_tokens", 0)
        
        if total_tokens > self.cfg.token_threshold_hourly:
            from ulid import ULID
            return RiskEvent(
                event_id=str(ULID()),
                request_id=audit_log.get("request_id", ""),
                user_id=audit_log.get("user_id", 0),
                user_name=audit_log.get("user_name", ""),
                risk_level=RiskLevel.HIGH.value,
                risk_type=RiskType.TOKEN_ABUSE.value,
                risk_score=0.8,
                risk_reason="单次请求token数超过阈值",
                description="用户单次请求使用了大量token",
                evidence={
                    "total_tokens": total_tokens,
                    "threshold": self.cfg.token_threshold_hourly,
                },
                request_ip=audit_log.get("request_ip", ""),
                model_name=audit_log.get("model_name", ""),
            )
        return None
    
    def _detect_off_hours(self, audit_log: dict) -> Optional[RiskEvent]:
        """Detect off-hours access."""
        request_time = audit_log.get("request_time")
        if not request_time:
            return None
        
        if isinstance(request_time, str):
            from dateutil import parser
            request_time = parser.parse(request_time)
        
        hour = request_time.hour
        
        # Check off-hours
        is_off_hours = False
        if self.cfg.off_hours_end < self.cfg.off_hours_start:
            # Cross midnight, e.g., 22:00 - 06:00
            is_off_hours = hour >= self.cfg.off_hours_start or hour < self.cfg.off_hours_end
        else:
            is_off_hours = self.cfg.off_hours_start <= hour < self.cfg.off_hours_end
        
        if is_off_hours:
            from ulid import ULID
            return RiskEvent(
                event_id=str(ULID()),
                request_id=audit_log.get("request_id", ""),
                user_id=audit_log.get("user_id", 0),
                user_name=audit_log.get("user_name", ""),
                risk_level=RiskLevel.LOW.value,
                risk_type=RiskType.OFF_HOURS_ACCESS.value,
                risk_score=0.3,
                risk_reason="非工作时间访问",
                description="用户在非工作时间使用AI服务",
                evidence={
                    "request_hour": hour,
                    "off_hours_start": self.cfg.off_hours_start,
                    "off_hours_end": self.cfg.off_hours_end,
                },
                request_ip=audit_log.get("request_ip", ""),
                model_name=audit_log.get("model_name", ""),
            )
        return None
    
    def _detect_sensitive_info(self, audit_log: dict) -> Optional[RiskEvent]:
        """Detect sensitive information access."""
        request_body = audit_log.get("request_body", "").lower()
        
        matched_keywords = []
        for keyword in DEFAULT_SENSITIVE_KEYWORDS:
            if keyword in request_body:
                matched_keywords.append(keyword)
        
        if matched_keywords:
            from ulid import ULID
            
            # Determine risk level based on keyword count
            if len(matched_keywords) >= 3:
                risk_level = RiskLevel.HIGH.value
                score = 0.8
            else:
                risk_level = RiskLevel.MEDIUM.value
                score = 0.5
            
            return RiskEvent(
                event_id=str(ULID()),
                request_id=audit_log.get("request_id", ""),
                user_id=audit_log.get("user_id", 0),
                user_name=audit_log.get("user_name", ""),
                risk_level=risk_level,
                risk_type=RiskType.SENSITIVE_INFO.value,
                risk_score=score,
                risk_reason="尝试获取敏感信息",
                description="用户请求中可能包含敏感信息获取意图",
                evidence={"matched_keywords": matched_keywords},
                request_ip=audit_log.get("request_ip", ""),
                model_name=audit_log.get("model_name", ""),
            )
        return None
    
    def _detect_ip_anomaly(self, audit_log: dict) -> Optional[RiskEvent]:
        """Detect IP anomaly."""
        request_ip = audit_log.get("request_ip", "")
        
        if request_ip in self.cfg.suspicious_ip_list:
            from ulid import ULID
            return RiskEvent(
                event_id=str(ULID()),
                request_id=audit_log.get("request_id", ""),
                user_id=audit_log.get("user_id", 0),
                user_name=audit_log.get("user_name", ""),
                risk_level=RiskLevel.HIGH.value,
                risk_type=RiskType.IP_ANOMALY.value,
                risk_score=0.9,
                risk_reason="可疑IP访问",
                description="请求来自可疑IP地址",
                evidence={
                    "ip": request_ip,
                    "suspicious_list": self.cfg.suspicious_ip_list,
                },
                request_ip=request_ip,
                model_name=audit_log.get("model_name", ""),
            )
        return None
    
    def _detect_abnormal_pattern(self, audit_log: dict) -> Optional[RiskEvent]:
        """Detect abnormal patterns and prompt injection."""
        request_body = audit_log.get("request_body", "").lower()
        
        matched_patterns = []
        
        # Check injection patterns
        for pattern in DEFAULT_INJECTION_PATTERNS:
            if re.search(pattern, request_body, re.IGNORECASE):
                matched_patterns.append(f"注入模式: {pattern}")
        
        if matched_patterns:
            from ulid import ULID
            return RiskEvent(
                event_id=str(ULID()),
                request_id=audit_log.get("request_id", ""),
                user_id=audit_log.get("user_id", 0),
                user_name=audit_log.get("user_name", ""),
                risk_level=RiskLevel.HIGH.value,
                risk_type=RiskType.ABNORMAL_PATTERN.value,
                risk_score=0.85,
                risk_reason="异常请求模式",
                description="检测到异常的请求模式或潜在的提示词注入",
                evidence={"matched_patterns": matched_patterns},
                request_ip=audit_log.get("request_ip", ""),
                model_name=audit_log.get("model_name", ""),
            )
        return None
    
    def _merge_events(
        self,
        audit_log: dict,
        events: list[RiskEvent]
    ) -> RiskEvent:
        """Merge multiple risk events."""
        from ulid import ULID
        
        max_score = max(e.risk_score for e in events)
        risk_types = [e.risk_type for e in events]
        risk_reasons = [e.risk_reason for e in events]
        
        # Determine final risk level
        if max_score >= 0.8:
            final_level = RiskLevel.HIGH.value
        elif max_score >= 0.5:
            final_level = RiskLevel.MEDIUM.value
        else:
            final_level = RiskLevel.LOW.value
        
        return RiskEvent(
            event_id=str(ULID()),
            request_id=audit_log.get("request_id", ""),
            user_id=audit_log.get("user_id", 0),
            user_name=audit_log.get("user_name", ""),
            risk_level=final_level,
            risk_type=RiskType.MULTIPLE.value,
            risk_score=max_score,
            risk_reason="多个风险因素",
            description="检测到多个风险因素",
            evidence={
                "risk_types": risk_types,
                "risk_reasons": risk_reasons,
            },
            request_ip=audit_log.get("request_ip", ""),
            model_name=audit_log.get("model_name", ""),
        )


async def detect_frequency_risk(user_id: int, request_ip: str) -> Optional[RiskEvent]:
    """Detect abnormal request frequency using Redis."""
    r = await get_redis()
    
    key = f"freq:user:{user_id}"
    count = await r.incr(key)
    await r.expire(key, 300)  # 5 minutes
    
    if count > 100:
        from ulid import ULID
        
        risk_level = RiskLevel.HIGH.value if count > 300 else RiskLevel.MEDIUM.value
        
        return RiskEvent(
            event_id=str(ULID()),
            request_id="",
            user_id=user_id,
            user_name="",
            risk_level=risk_level,
            risk_type=RiskType.ABNORMAL_FREQUENCY.value,
            risk_score=0.7 if count > 300 else 0.5,
            risk_reason="异常请求频率",
            description="用户短时间内发送了大量请求",
            evidence={"requests_in_5min": count, "threshold": 100},
            request_ip=request_ip,
            model_name=""
        )
    return None


def process_audit_log(audit_log: dict) -> None:
    """Process audit log and detect risks."""
    detector = RiskDetector()
    risk_event = detector.detect(audit_log)
    
    if risk_event:
        # Insert to ClickHouse
        insert_risk_event(risk_event.to_dict())
        
        # Log warning
        import logging
        logging.warning(
            f"Risk detected: {risk_event.risk_type} "
            f"(level={risk_event.risk_level}, user={risk_event.user_id})"
        )

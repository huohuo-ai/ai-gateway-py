"""Application constants."""
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    BANNED = "banned"


class ModelProvider(str, Enum):
    OPENAI = "openai"
    AZURE = "azure"
    ANTHROPIC = "anthropic"


class ModelStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskType(str, Enum):
    TOKEN_ABUSE = "token_abuse"
    OFF_HOURS_ACCESS = "off_hours_access"
    SENSITIVE_INFO = "sensitive_info"
    ABNORMAL_FREQUENCY = "abnormal_frequency"
    IP_ANOMALY = "ip_anomaly"
    ABNORMAL_PATTERN = "abnormal_pattern"
    MULTIPLE = "multiple"


class PatternType(str, Enum):
    SENSITIVE_INFO = "sensitive_info"
    ABNORMAL_PATTERN = "abnormal_pattern"
    INJECTION = "injection"


# Default sensitive keywords for risk detection
DEFAULT_SENSITIVE_KEYWORDS = [
    "password", "secret", "key", "token", "credential",
    "密码", "密钥", "机密", "隐私",
    "身份证", "手机号", "银行卡", "信用卡",
    "工资", "薪资", "salary", "income",
    "内部文件", "internal document", "confidential",
]

# Default prompt injection patterns
DEFAULT_INJECTION_PATTERNS = [
    r"ignore\s+previous\s+instructions",
    r"ignore\s+all\s+prior\s+instructions",
    r"disregard\s+previous",
    r"system\s+prompt",
    r"you\s+are\s+now",
    r"new\s+role",
    r"developer\s+mode",
    r"DAN\s+mode",
    r"jailbreak",
    r"DAN\s+",
]

# API Key prefix
API_KEY_PREFIX = "ak-"

# Request ID header
REQUEST_ID_HEADER = "X-Request-ID"

# Max content length for audit logs
MAX_AUDIT_CONTENT_LENGTH = 10000

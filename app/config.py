"""Configuration management using Pydantic Settings."""
from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerConfig(BaseSettings):
    port: int = 8080
    debug: bool = False
    reload: bool = False


class DatabaseConfig(BaseSettings):
    driver: str = "mysql+aiomysql"
    host: str = "localhost"
    port: int = 3306
    username: str = "root"
    password: str = "password"
    database: str = "ai_gateway"
    pool_size: int = 10
    max_overflow: int = 20

    @property
    def async_url(self) -> str:
        return f"{self.driver}://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


class RedisConfig(BaseSettings):
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    decode_responses: bool = True


class ClickHouseConfig(BaseSettings):
    host: str = "localhost"
    port: int = 8123
    database: str = "ai_gateway"
    username: str = "default"
    password: Optional[str] = None


class JWTConfig(BaseSettings):
    secret: str = "your-secret-key"
    algorithm: str = "HS256"
    expires_in: int = 86400  # 24 hours


class AuditConfig(BaseSettings):
    off_hours_start: int = 22
    off_hours_end: int = 6
    token_threshold_hourly: int = 100000
    suspicious_ip_list: List[str] = Field(default_factory=list)


class DefaultQuotaConfig(BaseSettings):
    daily_limit: int = 100000
    weekly_limit: int = 500000
    monthly_limit: int = 2000000


class RateLimitConfig(BaseSettings):
    requests_per_minute: int = 60


class LLMConfig(BaseSettings):
    default_timeout: int = 60
    max_retries: int = 3


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        yaml_file="config.yaml",
        yaml_file_encoding="utf-8",
        extra="ignore"
    )

    server: ServerConfig = Field(default_factory=ServerConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    clickhouse: ClickHouseConfig = Field(default_factory=ClickHouseConfig)
    jwt: JWTConfig = Field(default_factory=JWTConfig)
    audit: AuditConfig = Field(default_factory=AuditConfig)
    default_quota: DefaultQuotaConfig = Field(default_factory=DefaultQuotaConfig)
    rate_limit: RateLimitConfig = Field(default_factory=RateLimitConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()

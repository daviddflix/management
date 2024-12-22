from pydantic_settings import BaseSettings
from typing import List, Dict, Optional
import os

class Settings(BaseSettings):
    # Application Settings
    APP_NAME: str = "Dev Team Manager"
    PROJECT_DESCRIPTION: str = "A comprehensive team management system"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = os.getenv("ENVIRONMENT")
    
    # Monday.com Settings
    MONDAY_API_KEY: str
    MONDAY_API_URL: str = "https://api.monday.com/v2"
    MONDAY_BOARD_IDS: str = '["default_board_id"]'  # JSON string of board IDs
    MONDAY_DEFAULT_BOARD_ID: str = "default_board_id"
    MONDAY_RATE_LIMIT: int = 30  # API rate limit per minute
    
    # Slack Settings
    SLACK_BOT_TOKEN: str
    SLACK_DEFAULT_CHANNEL: str = "general"
    SLACK_TEAM_CHANNEL: str = "team"
    SLACK_PROJECT_CHANNEL: str = "project"
    SLACK_ALERTS_CHANNEL: str = "alerts"
    SLACK_REPORTS_CHANNEL: str = "reports"
    SLACK_ANNOUNCEMENTS_CHANNEL: str = "announcements"
    SLACK_TEAM_LEADS_CHANNEL: str = "#team-leads"
    SLACK_NOTIFICATION_LEVELS: str = "INFO,WARNING,ERROR"
    
    # API Keys and Security
    OPENAI_API_KEY: str
    SECRET_KEY: str
    ALGORITHM: str = os.getenv("ALGORITHM")
    # Security Settings
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PASSWORD_MIN_LENGTH: int = 8
    FAILED_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 15
    MAX_LOGIN_ATTEMPTS: int = 5  # Added for auth endpoint
    LOGIN_TIMEOUT_MINUTES: int = 15  # Added for auth endpoint
    
    # API URLs and Endpoints
    API_V1_PREFIX: str = "/api/v1"
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"

    # CORS Settings
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173"]
    ALLOWED_METHODS: List[str] = ["*"]
    ALLOWED_HEADERS: List[str] = ["*"]
    ALLOW_CREDENTIALS: bool = True
    
    # Database Settings
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 1800
    DB_CONNECT_RETRIES: int = 3
    
    # Redis Settings (for caching and rate limiting)
    REDIS_URL: str = os.getenv("REDIS_URL")
    REDIS_MAX_CONNECTIONS: int = 10
    REDIS_TIMEOUT: int = 30
    REDIS_RETRY_ON_TIMEOUT: bool = True
    REDIS_HEALTH_CHECK_INTERVAL: int = 30
    CACHE_TTL_SECONDS: int = 300
    
    # Session Settings
    SESSION_SECRET_KEY: str
    SESSION_COOKIE_NAME: str = "session"
    SESSION_COOKIE_SECURE: bool = True
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "lax"
    SESSION_EXPIRE_MINUTES: int = 60
    
    # OpenAI Settings
    OPENAI_ASSISTANT_MODEL: str = "gpt-4o"
    OPENAI_MAX_TOKENS: int = 4000
    OPENAI_TEMPERATURE: float = 0.5

    # Scheduler Settings
    SCHEDULER_TIMEZONE: str = "UTC"
    DAILY_UPDATE_TIME: str = "09:00"
    SPRINT_REMINDER_DAY: str = "FRIDAY"
    TASK_UPDATE_INTERVAL: int = 4  # hours
    SCHEDULER_MAX_INSTANCES: int = 3
    SCHEDULER_MISFIRE_GRACE_TIME: int = 60  # seconds
    
    # Team Settings
    DEFAULT_TEAM_TIMEZONE: str = "UTC"
    MAX_TEAM_SIZE: int = 10
    MIN_TEAM_SIZE: int = 2
    
    # Sprint Settings
    DEFAULT_SPRINT_DURATION: int = 14  # days
    MAX_SPRINT_STORY_POINTS: int = 10
    MIN_SPRINT_STORY_POINTS: int = 1
    
    # Logging Settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = "app.log"
    ENABLE_ACCESS_LOG: bool = True
    
    # Monitoring and Metrics
    ENABLE_METRICS: bool = True
    METRICS_UPDATE_INTERVAL: int = 60  # seconds
    PROMETHEUS_ENABLED: bool = True

    # Email Settings (for notifications)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAIL_FROM_NAME: str = "Dev Team Manager"
    EMAIL_ENABLED: bool = False
    
    # File Upload Settings
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = [".pdf", ".doc", ".docx", ".txt"]
    UPLOAD_PATH: str = "uploads"
    
    # Feature Flags
    ENABLE_AI_SUGGESTIONS: bool = True
    ENABLE_AUTO_ASSIGNMENTS: bool = True
    ENABLE_METRICS_DASHBOARD: bool = True
    ENABLE_SLACK_NOTIFICATIONS: bool = True
    ENABLE_EMAIL_NOTIFICATIONS: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def fastapi_kwargs(self) -> dict:
        """Settings to pass to FastAPI constructor"""
        return {
            "debug": self.DEBUG,
            "docs_url": self.DOCS_URL,
            "redoc_url": self.REDOC_URL,
            "title": self.APP_NAME,
            "version": self.APP_VERSION,
            "openapi_url": f"{self.API_V1_PREFIX}/openapi.json"
        }

settings = Settings() 
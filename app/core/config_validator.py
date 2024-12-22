from typing import Dict, Any, List
from pydantic import field_validator
from datetime import datetime
import re
import secrets

class ConfigValidator:
    @field_validator("SECRET_KEY", "SESSION_SECRET_KEY", mode="before")
    @classmethod
    def validate_secret_keys(cls, v: str) -> str:
        if v in ["your-secret-key-here", "your-session-secret-key"]:
            if not cls.Config.env_file:  # If not in development
                raise ValueError("Secret keys must be changed in production")
        return v

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        pattern = r'^postgresql\+asyncpg:\/\/[^:]+:[^@]+@[^:]+:\d+\/[^/]+$'
        if not re.match(pattern, v):
            raise ValueError("Invalid database URL format")
        return v

    @field_validator("OPENAI_API_KEY")
    def validate_openai_key(cls, v: str) -> str:
        if not v.startswith(('sk-', 'org-')):
            raise ValueError("Invalid OpenAI API key format")
        return v

    @field_validator("MONDAY_API_KEY")
    def validate_monday_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("Monday.com API key seems too short")
        return v

    @field_validator("ALLOWED_ORIGINS")
    def validate_origins(cls, v: List[str]) -> List[str]:
        for origin in v:
            if not origin.startswith(('http://', 'https://')):
                raise ValueError(f"Invalid origin format: {origin}")
        return v

    @field_validator("EMAIL_ENABLED")
    def validate_email_settings(cls, v: bool, values: Dict[str, Any]) -> bool:
        if v:
            required_fields = ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD"]
            missing = [f for f in required_fields if not values.get(f)]
            if missing:
                raise ValueError(f"Email enabled but missing: {', '.join(missing)}")
        return v

    @classmethod
    def generate_secret_key(cls) -> str:
        """Generate a secure secret key"""
        return secrets.token_urlsafe(32)

    @classmethod
    def validate_all_settings(cls, settings: Dict[str, Any]) -> Dict[str, str]:
        """Validate all settings and return any issues"""
        issues = {}
        
        # Check required settings
        required_settings = [
            "MONDAY_API_KEY",
            "SLACK_BOT_TOKEN",
            "OPENAI_API_KEY",
            "SECRET_KEY",
            "DATABASE_URL"
        ]
        
        for setting in required_settings:
            if not settings.get(setting):
                issues[setting] = "Required setting is missing"

        # Check security settings in production
        if settings.get("ENVIRONMENT") == "production":
            if not settings.get("SESSION_COOKIE_SECURE"):
                issues["SESSION_COOKIE_SECURE"] = "Must be True in production"
            if not settings.get("SENTRY_DSN"):
                issues["SENTRY_DSN"] = "Recommended for production monitoring"

        return issues 
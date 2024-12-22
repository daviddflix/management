import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import json
from typing import Any, Dict, Optional
from functools import wraps
import time
import traceback

# Configure logging format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
JSON_LOG_FORMAT = {
    "timestamp": "%(asctime)s",
    "name": "%(name)s",
    "level": "%(levelname)s",
    "message": "%(message)s",
    "module": "%(module)s",
    "function": "%(funcName)s",
    "line": "%(lineno)d"
}

class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            key: self._format_value(record, value)
            for key, value in JSON_LOG_FORMAT.items()
        }
        
        # Add extra fields if they exist
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        return json.dumps(log_data)
    
    def _format_value(self, record: logging.LogRecord, format_string: str) -> str:
        """Format a single value using the record information"""
        return format_string % record.__dict__

class AppLogger:
    """Centralized logging configuration for the application"""
    
    def __init__(
        self,
        name: str,
        log_level: str = "INFO",
        log_to_file: bool = True,
        log_dir: str = "logs",
        json_format: bool = True,
        max_bytes: int = 10485760,  # 10MB
        backup_count: int = 5
    ):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Create log directory if it doesn't exist
        if log_to_file:
            Path(log_dir).mkdir(parents=True, exist_ok=True)
        
        # Clear any existing handlers
        self.logger.handlers = []
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        if json_format:
            console_handler.setFormatter(JsonFormatter())
        else:
            console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        self.logger.addHandler(console_handler)
        
        if log_to_file:
            # File handler for all logs
            file_handler = RotatingFileHandler(
                f"{log_dir}/app.log",
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            if json_format:
                file_handler.setFormatter(JsonFormatter())
            else:
                file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
            self.logger.addHandler(file_handler)
            
            # Error file handler
            error_handler = RotatingFileHandler(
                f"{log_dir}/error.log",
                maxBytes=max_bytes,
                backupCount=backup_count
            )
            error_handler.setLevel(logging.ERROR)
            if json_format:
                error_handler.setFormatter(JsonFormatter())
            else:
                error_handler.setFormatter(logging.Formatter(LOG_FORMAT))
            self.logger.addHandler(error_handler)
    
    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance"""
        return self.logger

def log_execution_time(logger: Optional[logging.Logger] = None):
    """Decorator to log function execution time"""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                execution_time = time.time() - start_time
                log_message = {
                    "function": func.__name__,
                    "execution_time": f"{execution_time:.2f}s",
                    "status": "success"
                }
                if logger:
                    logger.info(json.dumps(log_message))
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                log_message = {
                    "function": func.__name__,
                    "execution_time": f"{execution_time:.2f}s",
                    "status": "error",
                    "error": str(e)
                }
                if logger:
                    logger.error(json.dumps(log_message))
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                log_message = {
                    "function": func.__name__,
                    "execution_time": f"{execution_time:.2f}s",
                    "status": "success"
                }
                if logger:
                    logger.info(json.dumps(log_message))
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                log_message = {
                    "function": func.__name__,
                    "execution_time": f"{execution_time:.2f}s",
                    "status": "error",
                    "error": str(e)
                }
                if logger:
                    logger.error(json.dumps(log_message))
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator

class RequestLogger:
    """Logger for HTTP requests and responses"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        body: Optional[Any] = None
    ):
        """Log HTTP request details"""
        log_data = {
            "type": "request",
            "method": method,
            "url": url,
            "headers": headers
        }
        if body:
            log_data["body"] = body
        self.logger.info(json.dumps(log_data))
    
    def log_response(
        self,
        status_code: int,
        headers: Dict[str, str],
        body: Optional[Any] = None,
        execution_time: Optional[float] = None
    ):
        """Log HTTP response details"""
        log_data = {
            "type": "response",
            "status_code": status_code,
            "headers": headers
        }
        if body:
            log_data["body"] = body
        if execution_time:
            log_data["execution_time"] = f"{execution_time:.2f}s"
        self.logger.info(json.dumps(log_data))

class MetricsLogger:
    """Logger for application metrics"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_metric(
        self,
        metric_name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ):
        """Log a metric with optional tags"""
        log_data = {
            "type": "metric",
            "name": metric_name,
            "value": value,
            "timestamp": datetime.utcnow().isoformat()
        }
        if tags:
            log_data["tags"] = tags
        self.logger.info(json.dumps(log_data))

# Create default application logger
app_logger = AppLogger(
    name="fastapi_app",
    log_level="INFO",
    log_to_file=True,
    json_format=True
).get_logger()

# Create request logger
request_logger = RequestLogger(app_logger)

# Create metrics logger
metrics_logger = MetricsLogger(app_logger)

# Example usage:
# from app.core.logging import app_logger, request_logger, metrics_logger, log_execution_time
#
# @log_execution_time(app_logger)
# async def some_function():
#     app_logger.info("Starting operation")
#     # ... function code ...
#     app_logger.info("Operation completed")
#
# # Log HTTP request/response
# request_logger.log_request("GET", "/api/users", {"Authorization": "Bearer ..."})
# request_logger.log_response(200, {"Content-Type": "application/json"}, {"data": "..."})
#
# # Log metrics
# metrics_logger.log_metric("api_response_time", 0.123, {"endpoint": "/api/users"})

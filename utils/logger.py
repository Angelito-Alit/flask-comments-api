import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from flask import request, g, current_app
from functools import wraps
import os

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add extra fields if they exist
        if hasattr(record, 'extra_data'):
            log_entry.update(record.extra_data)
        
        return json.dumps(log_entry)

class APILogger:
    """Centralized logging for API operations"""
    
    @staticmethod
    def setup_logger(app):
        """Configure application logging"""
        handler = logging.StreamHandler(sys.stdout)
        
        if app.config.get('LOG_FORMAT') == 'json':
            handler.setFormatter(JSONFormatter())
        else:
            handler.setFormatter(logging.Formatter(
                '%(asctime)s %(levelname)s: %(message)s'
            ))
        
        app.logger.addHandler(handler)
        app.logger.setLevel(getattr(logging, app.config.get('LOG_LEVEL', 'INFO')))
    
    @staticmethod
    def log_request():
        """Log incoming request details"""
        if current_app.config.get('LOG_REQUESTS', False):
            current_app.logger.info("Request received", extra={
                'extra_data': {
                    'method': request.method,
                    'path': request.path,
                    'remote_addr': request.remote_addr,
                    'user_agent': request.headers.get('User-Agent', '')
                }
            })
    
    @staticmethod
    def log_response(response):
        """Log outgoing response details"""
        if current_app.config.get('LOG_RESPONSES', False):
            current_app.logger.info("Response sent", extra={
                'extra_data': {
                    'status_code': response.status_code,
                    'content_type': response.content_type
                }
            })
        return response
    
    @staticmethod
    def log_security_event(event_type: str, details: Dict[str, Any]):
        """Log security-related events"""
        current_app.logger.warning(f"Security event: {event_type}", extra={
            'extra_data': {
                'event_type': event_type,
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'timestamp': datetime.utcnow().isoformat(),
                **details
            }
        })

def log_function_call(func):
    """Decorator to log function calls for debugging"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if current_app.config.get('LOG_FUNCTION_CALLS', False):
            current_app.logger.debug(f"Calling function: {func.__name__}")
        result = func(*args, **kwargs)
        return result
    return wrapper
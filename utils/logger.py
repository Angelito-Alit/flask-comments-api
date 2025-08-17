import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any
from flask import current_app

def setup_logging(app):
    """Setup logging configuration for the Flask application"""
    handler = logging.StreamHandler(sys.stdout)
    
    if app.config.get('LOG_FORMAT') == 'json':
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s'
        ))
    
    app.logger.addHandler(handler)
    app.logger.setLevel(getattr(logging, app.config.get('LOG_LEVEL', 'INFO')))

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
    def log_security_event(event_type: str, details: Dict[str, Any]):
        """Log security-related events"""
        if current_app:
            current_app.logger.warning(f"Security event: {event_type}", extra={
                'extra_data': {
                    'event_type': event_type,
                    'timestamp': datetime.utcnow().isoformat(),
                    **details
                }
            })
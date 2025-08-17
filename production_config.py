# production_config.py
import os
import logging
from datetime import timedelta

class ProductionConfig:
    """Production environment configuration with enhanced security and performance settings."""
    
    # Core Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'production-secret-key-must-be-changed'
    DEBUG = False
    TESTING = False
    
    # API Configuration
    WEATHER_API_KEY = os.environ.get('WEATHER_API_KEY', 'production-weather-key')
    API_RATE_LIMIT = int(os.environ.get('API_RATE_LIMIT', '50'))
    
    # Database Configuration (if needed in future)
    DATABASE_URL = os.environ.get('DATABASE_URL', '')
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT', 'true').lower() == 'true'
    
    # CORS Configuration
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'https://your-frontend-domain.com').split(',')
    
    # Performance Settings
    SEND_FILE_MAX_AGE_DEFAULT = timedelta(hours=1)
    MAX_CONTENT_LENGTH = 1024 * 1024  # 1MB max file upload
    
    # Security Headers
    SECURITY_HEADERS = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains; preload',
        'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self'; font-src 'self'; object-src 'none'; media-src 'self'; frame-src 'none';",
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Permissions-Policy': 'camera=(), microphone=(), geolocation=()'
    }
    
    # Rate Limiting Configuration
    RATE_LIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')
    
    # Session Configuration
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    
    @staticmethod
    def init_app(app):
        """Initialize production-specific application settings."""
        # Configure logging for production
        if not app.debug and not app.testing:
            if ProductionConfig.LOG_TO_STDOUT:
                stream_handler = logging.StreamHandler()
                stream_handler.setLevel(logging.INFO)
                formatter = logging.Formatter(
                    '%(asctime)s %(levelname)s: %(message)s '
                    '[in %(pathname)s:%(lineno)d]'
                )
                stream_handler.setFormatter(formatter)
                app.logger.addHandler(stream_handler)
                app.logger.setLevel(logging.INFO)
                app.logger.info('Production Flask Comments API startup')

# Health Check Configuration
HEALTH_CHECK_CONFIG = {
    'checks': [
        'database_connection',
        'external_api_availability',
        'memory_usage',
        'disk_space'
    ],
    'timeout': 5,
    'retry_count': 3
}

# Monitoring Configuration
MONITORING_CONFIG = {
    'metrics_enabled': True,
    'error_tracking': True,
    'performance_monitoring': True,
    'log_requests': False,  # Disabled in production for performance
    'log_responses': False
}
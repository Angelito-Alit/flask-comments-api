import os
import time
import psutil
import logging
import requests
from datetime import datetime, timedelta
from flask import jsonify, current_app
from functools import wraps

class ProductionMonitor:
    """Production monitoring system for Flask Comments API."""
    
    def __init__(self, app=None):
        self.app = app
        self.start_time = datetime.utcnow()
        self.request_count = 0
        self.error_count = 0
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize monitoring with Flask application."""
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        app.teardown_appcontext(self._teardown_request)
    
    def _before_request(self):
        """Track request start time."""
        self.request_count += 1
    
    def _after_request(self, response):
        """Log response metrics."""
        if response.status_code >= 400:
            self.error_count += 1
        return response
    
    def _teardown_request(self, exception=None):
        """Handle request teardown."""
        if exception is not None:
            self.error_count += 1
            current_app.logger.error(f'Request error: {exception}')

class HealthChecker:
    """Comprehensive health checking system."""
    
    @staticmethod
    def check_system_health():
        """Perform comprehensive system health check."""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'checks': {}
        }
        
        # Memory usage check
        memory_check = HealthChecker._check_memory_usage()
        health_status['checks']['memory'] = memory_check
        
        # Disk usage check
        disk_check = HealthChecker._check_disk_usage()
        health_status['checks']['disk'] = disk_check
        
        # API dependencies check
        external_apis_check = HealthChecker._check_external_apis()
        health_status['checks']['external_apis'] = external_apis_check
        
        # Application specific checks
        app_check = HealthChecker._check_application_health()
        health_status['checks']['application'] = app_check
        
        # Determine overall health status
        if any(check.get('status') == 'unhealthy' for check in health_status['checks'].values()):
            health_status['status'] = 'unhealthy'
        elif any(check.get('status') == 'warning' for check in health_status['checks'].values()):
            health_status['status'] = 'warning'
        
        return health_status
    
    @staticmethod
    def _check_memory_usage():
        """Check system memory usage."""
        try:
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            status = 'healthy'
            if memory_percent > 90:
                status = 'unhealthy'
            elif memory_percent > 80:
                status = 'warning'
            
            return {
                'status': status,
                'usage_percent': memory_percent,
                'available_mb': round(memory.available / 1024 / 1024, 2),
                'total_mb': round(memory.total / 1024 / 1024, 2)
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    @staticmethod
    def _check_disk_usage():
        """Check disk usage."""
        try:
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            status = 'healthy'
            if disk_percent > 90:
                status = 'unhealthy'
            elif disk_percent > 80:
                status = 'warning'
            
            return {
                'status': status,
                'usage_percent': round(disk_percent, 2),
                'free_gb': round(disk.free / 1024 / 1024 / 1024, 2),
                'total_gb': round(disk.total / 1024 / 1024 / 1024, 2)
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    @staticmethod
    def _check_external_apis():
        """Check external API dependencies."""
        external_checks = {}
        
        # Weather API check
        try:
            weather_api_key = os.environ.get('WEATHER_API_KEY', 'demo-key')
            if weather_api_key != 'demo-key':
                response = requests.get(
                    'http://api.openweathermap.org/data/2.5/weather',
                    params={'q': 'London', 'appid': weather_api_key},
                    timeout=5
                )
                external_checks['weather_api'] = {
                    'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                    'response_time_ms': response.elapsed.total_seconds() * 1000,
                    'status_code': response.status_code
                }
            else:
                external_checks['weather_api'] = {
                    'status': 'warning',
                    'message': 'Using demo mode'
                }
        except Exception as e:
            external_checks['weather_api'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        # JSONPlaceholder API check
        try:
            response = requests.get(
                'https://jsonplaceholder.typicode.com/posts/1',
                timeout=5
            )
            external_checks['jsonplaceholder_api'] = {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'response_time_ms': response.elapsed.total_seconds() * 1000,
                'status_code': response.status_code
            }
        except Exception as e:
            external_checks['jsonplaceholder_api'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
        
        return external_checks
    
    @staticmethod
    def _check_application_health():
        """Check application-specific health metrics."""
        try:
            # Check if the application is responding
            app_status = {
                'status': 'healthy',
                'flask_env': os.environ.get('FLASK_ENV', 'production'),
                'python_version': os.sys.version.split()[0],
                'uptime_seconds': (datetime.utcnow() - monitor.start_time).total_seconds() if 'monitor' in globals() else 0
            }
            
            return app_status
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }

def monitor_performance(f):
    """Decorator to monitor endpoint performance."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        try:
            result = f(*args, **kwargs)
            execution_time = (time.time() - start_time) * 1000
            
            current_app.logger.info(
                f'Endpoint {f.__name__} executed in {execution_time:.2f}ms'
            )
            return result
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            current_app.logger.error(
                f'Endpoint {f.__name__} failed after {execution_time:.2f}ms: {str(e)}'
            )
            raise
    return decorated_function

class MetricsCollector:
    """Collect and store application metrics."""
    
    def __init__(self):
        self.metrics = {
            'requests_total': 0,
            'requests_success': 0,
            'requests_error': 0,
            'response_times': [],
            'start_time': datetime.utcnow()
        }
    
    def record_request(self, status_code, response_time):
        """Record request metrics."""
        self.metrics['requests_total'] += 1
        
        if 200 <= status_code < 400:
            self.metrics['requests_success'] += 1
        else:
            self.metrics['requests_error'] += 1
        
        self.metrics['response_times'].append(response_time)
        
        # Keep only last 1000 response times
        if len(self.metrics['response_times']) > 1000:
            self.metrics['response_times'] = self.metrics['response_times'][-1000:]
    
    def get_metrics_summary(self):
        """Get metrics summary."""
        response_times = self.metrics['response_times']
        
        summary = {
            'requests_total': self.metrics['requests_total'],
            'requests_success': self.metrics['requests_success'],
            'requests_error': self.metrics['requests_error'],
            'success_rate': (
                self.metrics['requests_success'] / max(self.metrics['requests_total'], 1)
            ) * 100,
            'uptime_seconds': (datetime.utcnow() - self.metrics['start_time']).total_seconds()
        }
        
        if response_times:
            summary['response_time_stats'] = {
                'avg_ms': sum(response_times) / len(response_times),
                'min_ms': min(response_times),
                'max_ms': max(response_times),
                'count': len(response_times)
            }
        
        return summary

# Global instances
monitor = ProductionMonitor()
metrics_collector = MetricsCollector()
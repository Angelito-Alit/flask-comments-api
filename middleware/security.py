from flask import request, jsonify, current_app
from functools import wraps
import time
import re
from datetime import datetime

# Rate limiting storage
request_counts = {}

class SecurityMiddleware:
    """Security middleware for Flask applications"""
    
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize security middleware with Flask app"""
        app.after_request(self.add_security_headers)

    def add_security_headers(self, response):
        """Add security headers to responses"""
        if current_app.config.get('SECURITY_HEADERS'):
            for header, value in current_app.config['SECURITY_HEADERS'].items():
                response.headers[header] = value
        
        response.headers['X-API-Version'] = '1.0.0'
        response.headers['X-Timestamp'] = datetime.utcnow().isoformat()
        
        return response

def rate_limit(max_requests=100, window=3600):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Skip rate limiting in testing
            if current_app.config.get('TESTING'):
                return f(*args, **kwargs)
                
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            current_time = time.time()
            window_start = current_time - window
            
            # Clean old requests
            if client_ip in request_counts:
                request_counts[client_ip] = [
                    req_time for req_time in request_counts[client_ip] 
                    if req_time > window_start
                ]
            else:
                request_counts[client_ip] = []
            
            # Check rate limit
            if len(request_counts[client_ip]) >= max_requests:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Maximum {max_requests} requests per hour'
                }), 429
            
            request_counts[client_ip].append(current_time)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_json(required_fields=None):
    """JSON validation decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
            
            data = request.get_json()
            if data is None:
                return jsonify({'error': 'Invalid JSON'}), 400
            
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data or not data[field]]
                if missing_fields:
                    return jsonify({
                        'error': 'Missing required fields',
                        'missing_fields': missing_fields
                    }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def sanitize_input(text):
    """Sanitize user input by removing dangerous characters"""
    if not isinstance(text, str):
        return text
    
    # Remove HTML tags and dangerous characters
    text = re.sub(r'[<>"\']', '', text)
    
    # Limit length
    if len(text) > 500:
        text = text[:500]
    
    return text.strip()

def add_security_headers(response):
    """Add security headers to responses"""
    if current_app.config.get('SECURITY_HEADERS'):
        for header, value in current_app.config['SECURITY_HEADERS'].items():
            response.headers[header] = value
    
    response.headers['X-API-Version'] = '1.0.0'
    response.headers['X-Timestamp'] = datetime.utcnow().isoformat()
    
    return response
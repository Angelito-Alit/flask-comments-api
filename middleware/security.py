from flask import request, jsonify, current_app
from functools import wraps
import time
import logging
from datetime import datetime
import re

request_counts = {}

# Enforces request rate limiting per client IP
def rate_limit(max_requests=100, window=3600):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
            current_time = time.time()
            window_start = current_time - window
            # Keep only requests within the current time window
            if client_ip in request_counts:
                request_counts[client_ip] = [
                    req_time for req_time in request_counts[client_ip] 
                    if req_time > window_start
                ]
            else:
                request_counts[client_ip] = []
            
            # Reject if request limit exceeded
            if len(request_counts[client_ip]) >= max_requests:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Maximum {max_requests} requests per hour'
                }), 429
            
            request_counts[client_ip].append(current_time)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Validates incoming JSON payload and required fields
def validate_json(required_fields=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not request.is_json:
                return jsonify({'error': 'Content-Type must be application/json'}), 400
            
            data = request.get_json()
            if data is None:
                return jsonify({'error': 'Invalid JSON'}), 400
            
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return jsonify({
                        'error': 'Missing required fields',
                        'missing_fields': missing_fields
                    }), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Sanitizes user input by removing unsafe characters
def sanitize_input(text):
    if not isinstance(text, str):
        return text
    
    text = re.sub(r'[<>"\']', '', text)
    if len(text) > 500:
        text = text[:500]
    
    return text.strip()

# Adds security headers and metadata to HTTP responses
def add_security_headers(response):
    if current_app.config.get('SECURITY_HEADERS'):
        for header, value in current_app.config['SECURITY_HEADERS'].items():
            response.headers[header] = value
    
    response.headers['X-API-Version'] = '1.0.0'
    response.headers['X-Timestamp'] = datetime.utcnow().isoformat()
    
    return response

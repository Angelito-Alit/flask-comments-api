from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import html
import logging
import requests
import re
from datetime import datetime
from functools import wraps
import time

# Initialize Flask app
app = Flask(__name__)

# Load configuration based on environment
env = os.getenv('FLASK_ENV', 'development')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['DEBUG'] = env == 'development'
app.config['TESTING'] = env == 'testing'
app.config['LOG_LEVEL'] = os.environ.get('LOG_LEVEL', 'INFO')
app.config['WEATHER_API_KEY'] = os.environ.get('WEATHER_API_KEY', 'demo-key')

# Security headers configuration
app.config['SECURITY_HEADERS'] = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
    'Referrer-Policy': 'strict-origin-when-cross-origin'
}

# Enable CORS
CORS(app)

# Setup logging
logging.basicConfig(
    level=getattr(logging, app.config['LOG_LEVEL']),
    format='%(asctime)s %(levelname)s: %(message)s'
)

# Rate limiting storage
request_counts = {}

def rate_limit(max_requests=100, window=3600):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if app.config['TESTING']:
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
    """Sanitize user input"""
    if not isinstance(text, str):
        return text
    
    # Remove HTML tags and dangerous characters
    text = html.escape(text)
    text = re.sub(r'[<>"\']', '', text)
    
    # Limit length
    if len(text) > 500:
        text = text[:500]
    
    return text.strip()

def validate_comment_data(data):
    """Validate comment data"""
    if not data.get('author') or not data.get('author').strip():
        return {'valid': False, 'message': 'Author cannot be empty'}
    
    if not data.get('comment') or not data.get('comment').strip():
        return {'valid': False, 'message': 'Comment cannot be empty'}
    
    if len(data['author']) > 100:
        return {'valid': False, 'message': 'Author name too long (max 100 characters)'}
    
    if len(data['comment']) > 1000:
        return {'valid': False, 'message': 'Comment too long (max 1000 characters)'}
    
    return {'valid': True}

# In-memory storage for comments
comments_storage = [
    {
        "id": 1,
        "author": "John Doe",
        "comment": "This is a sample comment",
        "timestamp": "2024-01-15T10:30:00Z"
    },
    {
        "id": 2,
        "author": "Jane Smith", 
        "comment": "Another example comment",
        "timestamp": "2024-01-15T11:00:00Z"
    }
]

# Global counter for comment IDs
comment_counter = 2

@app.after_request
def after_request(response):
    """Add security headers to all responses"""
    if app.config.get('SECURITY_HEADERS'):
        for header, value in app.config['SECURITY_HEADERS'].items():
            response.headers[header] = value
    
    response.headers['X-API-Version'] = '1.0.0'
    response.headers['X-Timestamp'] = datetime.utcnow().isoformat()
    
    return response

@app.route('/', methods=['GET'])
@rate_limit(max_requests=200)
def home():
    """Home endpoint that provides API information."""
    return jsonify({
        "message": "Flask Comments API",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "environment": os.environ.get('FLASK_ENV', 'production'),
        "features": [
            "Comments CRUD API",
            "Weather integration", 
            "Rate limiting",
            "Input validation",
            "Security headers"
        ]
    }), 200

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "uptime": "available",
        "version": "1.0.0"
    }), 200

@app.route('/comments', methods=['GET'])
@rate_limit(max_requests=150)
def get_comments():
    """Get all comments."""
    try:
        app.logger.info(f"Fetching {len(comments_storage)} comments")
        return jsonify({
            "comments": comments_storage,
            "total": len(comments_storage),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }), 200
    except Exception as e:
        app.logger.error(f"Error fetching comments: {str(e)}")
        return jsonify({"error": "Failed to fetch comments"}), 500

@app.route('/comments', methods=['POST'])
@rate_limit(max_requests=50)
@validate_json(required_fields=['author', 'comment'])
def add_comment():
    """Add a new comment."""
    global comment_counter
    
    try:
        data = request.get_json()
        
        # Validate comment data
        validation_result = validate_comment_data(data)
        if not validation_result['valid']:
            return jsonify({"error": validation_result['message']}), 400
        
        # Sanitize input data
        sanitized_author = sanitize_input(data['author'])
        sanitized_comment = sanitize_input(data['comment'])
        
        # Create new comment
        comment_counter += 1
        new_comment = {
            "id": comment_counter,
            "author": sanitized_author,
            "comment": sanitized_comment,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        comments_storage.append(new_comment)
        app.logger.info(f"New comment added by {sanitized_author}")
        
        return jsonify({
            "message": "Comment added successfully",
            "comment": new_comment
        }), 201
        
    except Exception as e:
        app.logger.error(f"Error adding comment: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/comments/<int:comment_id>', methods=['GET'])
@rate_limit(max_requests=100)
def get_comment(comment_id):
    """Get a specific comment by ID."""
    try:
        comment = next((c for c in comments_storage if c['id'] == comment_id), None)
        
        if not comment:
            return jsonify({"error": "Comment not found"}), 404
        
        app.logger.info(f"Fetched comment {comment_id}")
        return jsonify(comment), 200
        
    except Exception as e:
        app.logger.error(f"Error fetching comment {comment_id}: {str(e)}")
        return jsonify({"error": "Failed to fetch comment"}), 500

@app.route('/comments/<int:comment_id>', methods=['DELETE'])
@rate_limit(max_requests=30)
def delete_comment(comment_id):
    """Delete a specific comment by ID."""
    global comments_storage
    
    try:
        comment = next((c for c in comments_storage if c['id'] == comment_id), None)
        
        if not comment:
            return jsonify({"error": "Comment not found"}), 404
        
        comments_storage = [c for c in comments_storage if c['id'] != comment_id]
        app.logger.info(f"Deleted comment {comment_id}")
        
        return jsonify({"message": f"Comment {comment_id} deleted successfully"}), 200
        
    except Exception as e:
        app.logger.error(f"Error deleting comment {comment_id}: {str(e)}")
        return jsonify({"error": "Failed to delete comment"}), 500

@app.route('/weather/<city>', methods=['GET'])
@rate_limit(max_requests=60)
def get_weather(city):
    """Demo weather endpoint that returns mock data."""
    try:
        # Sanitize city name
        sanitized_city = sanitize_input(city)
        
        # Validate city name format
        if not re.match(r"^[a-zA-ZÀ-ÿ\s\-']+$", sanitized_city):
            sanitized_city = re.sub(r'[^a-zA-ZÀ-ÿ\s\-\']', '', sanitized_city)
        
        api_key = app.config['WEATHER_API_KEY']
        
        if api_key == 'demo-key':
            # Return demo data
            weather_data = {
                "city": sanitized_city,
                "temperature": "22°C",
                "description": "Sunny",
                "humidity": "65%",
                "wind_speed": "15 km/h",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "note": "This is demo data for testing purposes"
            }
        else:
            # Make real API call
            url = f"http://api.openweathermap.org/data/2.5/weather"
            params = {
                'q': sanitized_city,
                'appid': api_key,
                'units': 'metric',
                'lang': 'en'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                weather_data = {
                    "city": data['name'],
                    "temperature": f"{data['main']['temp']}°C",
                    "description": data['weather'][0]['description'],
                    "humidity": f"{data['main']['humidity']}%",
                    "country": data['sys']['country']
                }
            else:
                return jsonify({"error": "City not found"}), 404
        
        app.logger.info(f"Weather data fetched for {sanitized_city}")
        return jsonify(weather_data), 200
        
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Weather API error: {str(e)}")
        return jsonify({"error": f"Weather API error: {str(e)}"}), 500
    except Exception as e:
        app.logger.error(f"Weather endpoint error: {str(e)}")
        return jsonify({"error": "Weather service unavailable"}), 500

@app.route('/api-demo', methods=['GET'])
@rate_limit(max_requests=80)
def api_demo():
    """API demonstration endpoint."""
    try:
        response = requests.get('https://jsonplaceholder.typicode.com/posts/1', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            app.logger.info("API demo data fetched successfully")
            return jsonify({
                "message": "API Demo Endpoint",
                "api_response": data,
                "source": "jsonplaceholder.typicode.com",
                "features": [
                    "RESTful API design",
                    "JSON responses",
                    "Input validation",
                    "Security headers",
                    "Error handling"
                ],
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }), 200
        else:
            return jsonify({"error": "External API error"}), 500
            
    except Exception as e:
        app.logger.error(f"API demo error: {str(e)}")
        return jsonify({"error": "Demo service unavailable"}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        "error": "Not Found",
        "message": "The requested resource was not found",
        "status_code": 404
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    return jsonify({
        "error": "Method Not Allowed",
        "message": "The method is not allowed for the requested URL",
        "status_code": 405
    }), 405

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    app.logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        "error": "Internal Server Error",
        "message": "An internal server error occurred",
        "status_code": 500
    }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug = app.config.get('DEBUG', False)
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
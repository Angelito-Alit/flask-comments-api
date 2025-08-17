from flask import Flask, jsonify, request
import requests
import os
import logging
from datetime import datetime
from config import config
from middleware.security import rate_limit, validate_json, sanitize_input, add_security_headers
from utils.validators import InputValidator, ValidationError

def create_app(config_name=None):
    """Application factory pattern"""
    app = Flask(__name__)
    
    # Configuración
    config_name = config_name or os.environ.get('FLASK_ENV', 'default')
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Configurar logging
    logging.basicConfig(
        level=getattr(logging, app.config['LOG_LEVEL']),
        format='%(asctime)s %(levelname)s: %(message)s'
    )
    
    # Middleware global
    @app.after_request
    def after_request(response):
        return add_security_headers(response)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found',
            'status_code': 404
        }), 404
    
    @app.errorhandler(429)
    def ratelimit_handler(error):
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': 'Too many requests',
            'status_code': 429
        }), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal error: {str(error)}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An internal server error occurred',
            'status_code': 500
        }), 500
    
    return app

# Crear instancia de la aplicación
app = create_app()

# Simulación de base de datos en memoria
comments_db = [
    {
        "id": 1,
        "author": "Juan Pérez",
        "comment": "Este es un comentario de ejemplo",
        "timestamp": "2024-01-15T10:30:00"
    },
    {
        "id": 2,
        "author": "María González",
        "comment": "Excelente proyecto de CI/CD",
        "timestamp": "2024-01-15T11:15:00"
    }
]

@app.route('/')
@rate_limit(max_requests=200)
def home():
    """Endpoint principal"""
    return jsonify({
        "message": "Flask Comments API - Proyecto Universitario",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "environment": os.environ.get('FLASK_ENV', 'production'),
        "features": [
            "Comments CRUD API",
            "Weather integration",
            "Rate limiting",
            "Input validation",
            "Security headers"
        ]
    })

@app.route('/health')
def health():
    """Health check endpoint para el deploy"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime": "available",
        "version": "1.0.0"
    }), 200

@app.route('/comments', methods=['GET'])
@rate_limit(max_requests=150)
def get_comments():
    """Obtener todos los comentarios"""
    try:
        app.logger.info(f"Fetching {len(comments_db)} comments")
        return jsonify({
            "comments": comments_db,
            "total": len(comments_db),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        app.logger.error(f"Error fetching comments: {str(e)}")
        return jsonify({"error": "Failed to fetch comments"}), 500

@app.route('/comments', methods=['POST'])
@rate_limit(max_requests=50)
@validate_json(required_fields=['author', 'comment'])
def add_comment():
    """Agregar un nuevo comentario"""
    try:
        data = request.get_json()
        
        # Validar y sanitizar usando InputValidator
        try:
            author = InputValidator.validate_author(data['author'])
            comment = InputValidator.validate_comment(data['comment'])
        except ValidationError as e:
            return jsonify({
                "error": "Validation error", 
                "message": e.message,
                "field": e.field
            }), 400
        
        new_comment = {
            "id": len(comments_db) + 1,
            "author": author,
            "comment": comment,
            "timestamp": datetime.now().isoformat()
        }
        
        comments_db.append(new_comment)
        app.logger.info(f"New comment added by {author}")
        
        return jsonify({
            "message": "Comentario agregado exitosamente",
            "comment": new_comment
        }), 201
        
    except Exception as e:
        app.logger.error(f"Error adding comment: {str(e)}")
        return jsonify({"error": "Failed to add comment"}), 500

@app.route('/comments/<int:comment_id>', methods=['GET'])
@rate_limit(max_requests=100)
def get_comment(comment_id):
    """Obtener un comentario específico"""
    try:
        comment = next((c for c in comments_db if c['id'] == comment_id), None)
        
        if not comment:
            return jsonify({"error": "Comentario no encontrado"}), 404
        
        app.logger.info(f"Fetched comment {comment_id}")
        return jsonify(comment)
        
    except Exception as e:
        app.logger.error(f"Error fetching comment {comment_id}: {str(e)}")
        return jsonify({"error": "Failed to fetch comment"}), 500

@app.route('/comments/<int:comment_id>', methods=['DELETE'])
@rate_limit(max_requests=30)
def delete_comment(comment_id):
    """Eliminar un comentario"""
    try:
        global comments_db
        
        comment = next((c for c in comments_db if c['id'] == comment_id), None)
        
        if not comment:
            return jsonify({"error": "Comentario no encontrado"}), 404
        
        comments_db = [c for c in comments_db if c['id'] != comment_id]
        app.logger.info(f"Deleted comment {comment_id}")
        
        return jsonify({"message": f"Comentario {comment_id} eliminado exitosamente"})
        
    except Exception as e:
        app.logger.error(f"Error deleting comment {comment_id}: {str(e)}")
        return jsonify({"error": "Failed to delete comment"}), 500

@app.route('/weather/<city>')
@rate_limit(max_requests=60)
def get_weather(city):
    """Endpoint que consume API externa - OpenWeatherMap"""
    try:
        # Validar nombre de ciudad
        try:
            city = InputValidator.validate_city_name(city)
        except ValidationError as e:
            return jsonify({
                "error": "Invalid city name",
                "message": e.message
            }), 400
        
        api_key = app.config['WEATHER_API_KEY']
        
        if api_key == 'demo-key':
            return jsonify({
                "city": city,
                "temperature": "22°C",
                "description": "Soleado",
                "humidity": "65%",
                "note": "Datos de demostración - configurar API_KEY real"
            })
        
        url = f"http://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': city,
            'appid': api_key,
            'units': 'metric',
            'lang': 'es'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            result = {
                "city": data['name'],
                "temperature": f"{data['main']['temp']}°C",
                "description": data['weather'][0]['description'],
                "humidity": f"{data['main']['humidity']}%",
                "country": data['sys']['country']
            }
            app.logger.info(f"Weather data fetched for {city}")
            return jsonify(result)
        else:
            return jsonify({"error": "Ciudad no encontrada"}), 404
            
    except requests.exceptions.RequestException as e:
        app.logger.error(f"Weather API error: {str(e)}")
        return jsonify({"error": f"Error al consultar API: {str(e)}"}), 500
    except Exception as e:
        app.logger.error(f"Weather endpoint error: {str(e)}")
        return jsonify({"error": "Weather service unavailable"}), 500

@app.route('/api-demo')
@rate_limit(max_requests=80)
def api_demo():
    """Demostración de consumo de API pública"""
    try:
        response = requests.get('https://jsonplaceholder.typicode.com/posts/1', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            app.logger.info("API demo data fetched successfully")
            return jsonify({
                "message": "Ejemplo de consumo de API externa",
                "api_response": data,
                "source": "jsonplaceholder.typicode.com"
            })
        else:
            return jsonify({"error": "Error al consumir API externa"}), 500
            
    except Exception as e:
        app.logger.error(f"API demo error: {str(e)}")
        return jsonify({"error": "Demo service unavailable"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])
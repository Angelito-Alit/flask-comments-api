from flask import Flask, jsonify, request
import requests
import os
from datetime import datetime

app = Flask(__name__)

# Configuración
API_KEY = os.environ.get('WEATHER_API_KEY', 'demo-key')

@app.route('/')
def home():
    """Endpoint principal"""
    return jsonify({
        "message": "Flask Comments API - Proyecto Universitario",
        "status": "running",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

@app.route('/health')
def health():
    """Health check endpoint para el deploy"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }), 200

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

@app.route('/comments', methods=['GET'])
def get_comments():
    """Obtener todos los comentarios"""
    return jsonify({
        "comments": comments_db,
        "total": len(comments_db)
    })

@app.route('/comments', methods=['POST'])
def add_comment():
    """Agregar un nuevo comentario"""
    try:
        data = request.get_json()
        
        if not data or 'author' not in data or 'comment' not in data:
            return jsonify({"error": "Se requieren 'author' y 'comment'"}), 400
        
        new_comment = {
            "id": len(comments_db) + 1,
            "author": data['author'],
            "comment": data['comment'],
            "timestamp": datetime.now().isoformat()
        }
        
        comments_db.append(new_comment)
        
        return jsonify({
            "message": "Comentario agregado exitosamente",
            "comment": new_comment
        }), 201
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/comments/<int:comment_id>', methods=['GET'])
def get_comment(comment_id):
    """Obtener un comentario específico"""
    comment = next((c for c in comments_db if c['id'] == comment_id), None)
    
    if not comment:
        return jsonify({"error": "Comentario no encontrado"}), 404
    
    return jsonify(comment)

@app.route('/comments/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    """Eliminar un comentario"""
    global comments_db
    
    comment = next((c for c in comments_db if c['id'] == comment_id), None)
    
    if not comment:
        return jsonify({"error": "Comentario no encontrado"}), 404
    
    comments_db = [c for c in comments_db if c['id'] != comment_id]
    
    return jsonify({"message": f"Comentario {comment_id} eliminado exitosamente"})

@app.route('/weather/<city>')
def get_weather(city):
    """Endpoint que consume API externa - OpenWeatherMap"""
    try:
        # API gratuita de ejemplo (requiere registro en openweathermap.org)
        if API_KEY == 'demo-key':
            # Datos de demostración
            return jsonify({
                "city": city,
                "temperature": "22°C",
                "description": "Soleado",
                "humidity": "65%",
                "note": "Datos de demostración - configurar API_KEY real"
            })
        
        # Llamada real a la API
        url = f"http://api.openweathermap.org/data/2.5/weather"
        params = {
            'q': city,
            'appid': API_KEY,
            'units': 'metric',
            'lang': 'es'
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                "city": data['name'],
                "temperature": f"{data['main']['temp']}°C",
                "description": data['weather'][0]['description'],
                "humidity": f"{data['main']['humidity']}%",
                "country": data['sys']['country']
            })
        else:
            return jsonify({"error": "Ciudad no encontrada"}), 404
            
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Error al consultar API: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api-demo')
def api_demo():
    """Demostración de consumo de API pública (sin autenticación)"""
    try:
        # JSONPlaceholder - API gratuita para testing
        response = requests.get('https://jsonplaceholder.typicode.com/posts/1', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                "message": "Ejemplo de consumo de API externa",
                "api_response": data,
                "source": "jsonplaceholder.typicode.com"
            })
        else:
            return jsonify({"error": "Error al consumir API externa"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Para desarrollo local
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
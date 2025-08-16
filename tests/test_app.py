import unittest
import json
from flask_testing import TestCase
from app import app

class FlaskAppTestCase(TestCase):
    
    def create_app(self):
        """Crear instancia de la app para testing"""
        app.config['TESTING'] = True
        return app
    
    def setUp(self):
        """Configuración antes de cada test"""
        from app import comments_db
        comments_db.clear()
        # Datos de prueba
        comments_db.extend([
            {
                "id": 1,
                "author": "Test User",
                "comment": "Test comment",
                "timestamp": "2024-01-15T10:30:00"
            }
        ])
    
    def test_home_endpoint(self):
        """Test del endpoint principal"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('message', data)
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'running')
    
    def test_health_endpoint(self):
        """Test del health check"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
    
    def test_get_comments(self):
        """Test para obtener comentarios"""
        response = self.client.get('/comments')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('comments', data)
        self.assertIn('total', data)
        self.assertEqual(data['total'], 1)
    
    def test_add_comment(self):
        """Test para agregar comentario"""
        new_comment = {
            "author": "Test Author",
            "comment": "This is a test comment"
        }
        
        response = self.client.post('/comments',
                                  data=json.dumps(new_comment),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        
        data = json.loads(response.data)
        self.assertIn('message', data)
        self.assertIn('comment', data)
        self.assertEqual(data['comment']['author'], 'Test Author')
    
    def test_add_comment_invalid_data(self):
        """Test para agregar comentario con datos inválidos"""
        invalid_comment = {"author": "Test Author"}  # Falta 'comment'
        
        response = self.client.post('/comments',
                                  data=json.dumps(invalid_comment),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_get_specific_comment(self):
        """Test para obtener comentario específico"""
        response = self.client.get('/comments/1')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['author'], 'Test User')
    
    def test_get_nonexistent_comment(self):
        """Test para obtener comentario inexistente"""
        response = self.client.get('/comments/999')
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_delete_comment(self):
        """Test para eliminar comentario"""
        response = self.client.delete('/comments/1')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('message', data)
        
        # Verificar que el comentario fue eliminado
        response = self.client.get('/comments/1')
        self.assertEqual(response.status_code, 404)
    
    def test_api_demo_endpoint(self):
        """Test del endpoint de demostración de API"""
        response = self.client.get('/api-demo')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('message', data)
        self.assertIn('api_response', data)
        self.assertIn('source', data)
    
    def test_weather_endpoint_demo(self):
        """Test del endpoint de clima (modo demo)"""
        response = self.client.get('/weather/Madrid')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('city', data)
        self.assertIn('temperature', data)
        self.assertEqual(data['city'], 'Madrid')

if __name__ == '__main__':
    unittest.main()
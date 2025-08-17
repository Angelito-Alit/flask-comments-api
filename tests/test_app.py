import unittest
import json
from flask_testing import TestCase
from app import create_app, comments_db
from config import TestingConfig

class FlaskAppTestCase(TestCase):
    
    def create_app(self):
        app = create_app('testing')
        return app
    
    def setUp(self):
        from app import comments_db
        comments_db.clear()
        comments_db.extend([
            {
                "id": 1,
                "author": "Test User",
                "comment": "Test comment",
                "timestamp": "2024-01-15T10:30:00"
            },
            {
                "id": 2,
                "author": "Another User",
                "comment": "Another test comment",
                "timestamp": "2024-01-15T11:30:00"
            }
        ])
    
    def test_home_endpoint(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('message', data)
        self.assertIn('status', data)
        self.assertIn('features', data)
        self.assertEqual(data['status'], 'running')
        self.assertIsInstance(data['features'], list)
    
    def test_health_endpoint(self):
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('timestamp', data)
        self.assertIn('version', data)
    
    def test_security_headers(self):
        response = self.client.get('/')
        self.assertIn('X-API-Version', response.headers)
        self.assertIn('X-Timestamp', response.headers)
        self.assertEqual(response.headers['X-API-Version'], '1.0.0')
    
    def test_get_comments(self):
        response = self.client.get('/comments')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('comments', data)
        self.assertIn('total', data)
        self.assertIn('timestamp', data)
        self.assertEqual(data['total'], 2)
        self.assertEqual(len(data['comments']), 2)
    
    def test_add_comment_valid(self):
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
        self.assertEqual(data['comment']['id'], 3)  
    
    def test_add_comment_missing_fields(self):
        invalid_comment = {"author": "Test Author"}  
        
        response = self.client.post('/comments',
                                  data=json.dumps(invalid_comment),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('missing_fields', data)
        self.assertIn('comment', data['missing_fields'])
    
    def test_add_comment_invalid_json(self):
        response = self.client.post('/comments',
                                  data="invalid json",
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_add_comment_empty_values(self):
        empty_comment = {
            "author": "",
            "comment": ""
        }
        
        response = self.client.post('/comments',
                                  data=json.dumps(empty_comment),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_input_sanitization(self):
        malicious_comment = {
            "author": "Test<script>alert('xss')</script>",
            "comment": "Comment with 'quotes' and <tags>"
        }
        
        response = self.client.post('/comments',
                                  data=json.dumps(malicious_comment),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        
        data = json.loads(response.data)
        self.assertNotIn('<script>', data['comment']['author'])
        self.assertNotIn('<tags>', data['comment']['comment'])
        self.assertNotIn("'", data['comment']['comment'])
    
    def test_get_specific_comment(self):
        response = self.client.get('/comments/1')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['author'], 'Test User')
    
    def test_get_nonexistent_comment(self):
        response = self.client.get('/comments/999')
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_delete_comment(self):
        response = self.client.get('/comments/1')
        self.assertEqual(response.status_code, 200)
        
        response = self.client.delete('/comments/1')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('message', data)
        
        response = self.client.get('/comments/1')
        self.assertEqual(response.status_code, 404)
    
    def test_delete_nonexistent_comment(self):
        response = self.client.delete('/comments/999')
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_api_demo_endpoint(self):
        response = self.client.get('/api-demo')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('message', data)
        self.assertIn('api_response', data)
        self.assertIn('source', data)
        self.assertEqual(data['source'], 'jsonplaceholder.typicode.com')
    
    def test_weather_endpoint_demo(self):
        response = self.client.get('/weather/Madrid')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('city', data)
        self.assertIn('temperature', data)
        self.assertIn('note', data) 
        self.assertEqual(data['city'], 'Madrid')
    
    def test_weather_endpoint_sanitization(self):
        response = self.client.get('/weather/Madrid<script>')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertNotIn('<script>', data['city'])
    
    def test_404_error_handler(self):
        response = self.client.get('/nonexistent')
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('message', data)
        self.assertEqual(data['status_code'], 404)
    
    def test_method_not_allowed(self):
        response = self.client.put('/comments') 
        self.assertEqual(response.status_code, 405)

class ConfigTestCase(unittest.TestCase):
    
    def test_development_config(self):
        app = create_app('development')
        self.assertTrue(app.config['DEBUG'])
        self.assertEqual(app.config['LOG_LEVEL'], 'DEBUG')
    
    def test_testing_config(self):
        app = create_app('testing')
        self.assertTrue(app.config['TESTING'])
        self.assertEqual(app.config['SECRET_KEY'], 'test-secret-key')
        self.assertEqual(app.config['API_RATE_LIMIT'], 1000)
    
    def test_production_config(self):
        app = create_app('production')
        self.assertFalse(app.config['DEBUG'])
        self.assertIn('SECURITY_HEADERS', app.config)

if __name__ == '__main__':
    unittest.main()
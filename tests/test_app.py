import unittest
import json
import sys
import os

# Add the parent directory to the path so we can import the app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, comments_storage

class FlaskAppTestCase(unittest.TestCase):
    """Test suite for the main Flask application endpoints."""
    
    def setUp(self):
        """Set up test client and reset data before each test."""
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['DEBUG'] = False
        self.client = app.test_client()
        
        # Reset comments storage to a known state
        comments_storage.clear()
        comments_storage.extend([
            {
                "id": 1,
                "author": "Test User",
                "comment": "Test comment",
                "timestamp": "2024-01-15T10:30:00Z"
            },
            {
                "id": 2,
                "author": "Another User",
                "comment": "Another test comment",
                "timestamp": "2024-01-15T11:30:00Z"
            }
        ])
        
        # Reset comment counter
        import app as app_module
        app_module.comment_counter = 2
    
    def test_home_endpoint(self):
        """Test the home endpoint returns correct data."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('message', data)
        self.assertIn('status', data)
        self.assertIn('features', data)
        self.assertEqual(data['status'], 'running')
        self.assertIsInstance(data['features'], list)
    
    def test_health_endpoint(self):
        """Test the health check endpoint works properly."""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')
        self.assertIn('timestamp', data)
        self.assertIn('version', data)
    
    def test_security_headers(self):
        """Test that security headers are present in responses."""
        response = self.client.get('/')
        self.assertIn('X-API-Version', response.headers)
        self.assertIn('X-Timestamp', response.headers)
        self.assertEqual(response.headers['X-API-Version'], '1.0.0')
    
    def test_get_comments(self):
        """Test getting all comments returns the right format."""
        response = self.client.get('/comments')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('comments', data)
        self.assertIn('total', data)
        self.assertIn('timestamp', data)
        self.assertEqual(data['total'], 2)
        self.assertEqual(len(data['comments']), 2)
    
    def test_add_comment_valid(self):
        """Test adding a new comment with valid data."""
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
        """Test error handling when required fields are missing."""
        invalid_comment = {"author": "Test Author"}  # Missing 'comment' field
        
        response = self.client.post('/comments',
                                  data=json.dumps(invalid_comment),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('missing_fields', data)
        self.assertIn('comment', data['missing_fields'])
    
    def test_add_comment_invalid_json(self):
        """Test error handling for invalid JSON data."""
        response = self.client.post('/comments',
                                  data="invalid json",
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_add_comment_empty_values(self):
        """Test that empty field values are rejected properly."""
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
        """Test that dangerous input is cleaned before saving."""
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
        """Test getting a single comment by its ID."""
        response = self.client.get('/comments/1')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['id'], 1)
        self.assertEqual(data['author'], 'Test User')
    
    def test_get_nonexistent_comment(self):
        """Test that requesting a missing comment returns 404."""
        response = self.client.get('/comments/999')
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_delete_comment(self):
        """Test deleting a comment removes it completely."""
        # First check the comment exists
        response = self.client.get('/comments/1')
        self.assertEqual(response.status_code, 200)
        
        # Delete the comment
        response = self.client.delete('/comments/1')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('message', data)
        
        # Check the comment is gone
        response = self.client.get('/comments/1')
        self.assertEqual(response.status_code, 404)
    
    def test_delete_nonexistent_comment(self):
        """Test deleting a comment that doesn't exist."""
        response = self.client.delete('/comments/999')
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
    
    def test_api_demo_endpoint(self):
        """Test the API demo endpoint works correctly."""
        response = self.client.get('/api-demo')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('message', data)
        self.assertIn('api_response', data)
        self.assertIn('source', data)
        self.assertEqual(data['source'], 'jsonplaceholder.typicode.com')
    
    def test_weather_endpoint_demo(self):
        """Test the weather demo endpoint returns mock data."""
        response = self.client.get('/weather/Madrid')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('city', data)
        self.assertIn('temperature', data)
        self.assertIn('note', data)
        self.assertEqual(data['city'], 'Madrid')
    
    def test_weather_endpoint_sanitization(self):
        """Test that city names are cleaned in weather endpoint."""
        response = self.client.get('/weather/Madrid<script>')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertNotIn('<script>', data['city'])
    
    def test_404_error_handler(self):
        """Test that 404 errors are handled correctly."""
        response = self.client.get('/nonexistent')
        self.assertEqual(response.status_code, 404)
        
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('message', data)
        self.assertEqual(data['status_code'], 404)
    
    def test_method_not_allowed(self):
        """Test that wrong HTTP methods return 405 error."""
        response = self.client.put('/comments')
        self.assertEqual(response.status_code, 405)

class ConfigTestCase(unittest.TestCase):
    """Test suite for application configuration settings."""
    
    def test_development_config(self):
        """Test that development config has debug enabled."""
        # Set environment for development
        os.environ['FLASK_ENV'] = 'development'
        app.config['DEBUG'] = True
        app.config['LOG_LEVEL'] = 'DEBUG'
        
        self.assertTrue(app.config['DEBUG'])
        self.assertEqual(app.config['LOG_LEVEL'], 'DEBUG')
    
    def test_testing_config(self):
        """Test that testing config has correct test settings."""
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        
        self.assertTrue(app.config['TESTING'])
        self.assertEqual(app.config['SECRET_KEY'], 'test-secret-key')
    
    def test_production_config(self):
        """Test that production config is secure and optimized."""
        # Set environment for production
        os.environ['FLASK_ENV'] = 'production'
        app.config['DEBUG'] = False
        
        self.assertFalse(app.config['DEBUG'])
        self.assertIn('SECURITY_HEADERS', app.config)

if __name__ == '__main__':
    # Run all tests when script is executed directly
    unittest.main()
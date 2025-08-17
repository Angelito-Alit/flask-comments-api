import re
import html
from typing import Dict, Any, Optional

class ValidationError(Exception):
    """Custom exception for validation errors"""
    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(self.message)

def sanitize_input(text):
    """Sanitize user input by removing dangerous characters"""
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
    """Validate comment data structure and content"""
    if not isinstance(data, dict):
        return {'valid': False, 'message': 'Data must be a dictionary'}
    
    # Check required fields exist and are not empty
    if not data.get('author') or not str(data.get('author')).strip():
        return {'valid': False, 'message': 'Author cannot be empty'}
    
    if not data.get('comment') or not str(data.get('comment')).strip():
        return {'valid': False, 'message': 'Comment cannot be empty'}
    
    # Check length limits
    if len(str(data['author'])) > 100:
        return {'valid': False, 'message': 'Author name too long (max 100 characters)'}
    
    if len(str(data['comment'])) > 1000:
        return {'valid': False, 'message': 'Comment too long (max 1000 characters)'}
    
    return {'valid': True}

class InputValidator:
    """Comprehensive input validation and sanitization"""
    
    @staticmethod
    def sanitize_string(text: str, max_length: int = 500) -> str:
        """Sanitize string input removing dangerous characters"""
        if not isinstance(text, str):
            return ""
        
        # Remove HTML tags and entities
        text = html.escape(text)
        text = re.sub(r'<[^>]*>', '', text)
        
        # Remove potentially dangerous characters
        text = re.sub(r'[<>"\'\`]', '', text)
        
        # Limit length
        if len(text) > max_length:
            text = text[:max_length]
        
        return text.strip()
    
    @staticmethod
    def validate_comment(comment: str) -> str:
        """Validate and sanitize comment input"""
        if not comment or len(comment.strip()) == 0:
            raise ValidationError("Comment cannot be empty", "comment")
        
        if len(comment) > 1000:
            raise ValidationError("Comment too long (max 1000 characters)", "comment")
        
        return InputValidator.sanitize_string(comment, 1000)
    
    @staticmethod
    def validate_author(author: str) -> str:
        """Validate and sanitize author name"""
        if not author or len(author.strip()) == 0:
            raise ValidationError("Author name cannot be empty", "author")
        
        if len(author) > 100:
            raise ValidationError("Author name too long (max 100 characters)", "author")
        
        # Check for suspicious patterns
        if re.search(r'(script|javascript|vbscript|onload|onerror)', author.lower()):
            raise ValidationError("Author name contains invalid content", "author")
        
        return InputValidator.sanitize_string(author, 100)
    
    @staticmethod
    def validate_city_name(city: str) -> str:
        """Validate city name for weather API"""
        if not city or len(city.strip()) == 0:
            raise ValidationError("City name cannot be empty", "city")
        
        # Only allow letters, spaces, hyphens, and apostrophes
        if not re.match(r"^[a-zA-ZÀ-ÿ\s\-']+$", city):
            raise ValidationError("Invalid city name format", "city")
        
        return InputValidator.sanitize_string(city, 50)
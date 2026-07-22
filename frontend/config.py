import os
from typing import Optional

class Config:
    """Configuration for the Flask application"""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # Server Configuration
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 8080))
    
    # Backend API Configuration
    BACKEND_API_URL = os.getenv('BACKEND_API_URL', 'http://localhost:5000/api')
    BACKEND_API_TIMEOUT = int(os.getenv('BACKEND_API_TIMEOUT', 10))
    
    # Auto-refresh Configuration
    AUTO_REFRESH_ENABLED = os.getenv('AUTO_REFRESH_ENABLED', 'True').lower() == 'true'
    AUTO_REFRESH_INTERVAL = int(os.getenv('AUTO_REFRESH_INTERVAL', 30))  # seconds
    
    # Display Configuration
    ITEMS_PER_PAGE = int(os.getenv('ITEMS_PER_PAGE', 20))
    MAX_HISTORY_ITEMS = int(os.getenv('MAX_HISTORY_ITEMS', 50))
    
    @staticmethod
    def validate_config() -> bool:
        """Validate that required configuration is present"""
        if not Config.BACKEND_API_URL:
            print("Warning: BACKEND_API_URL not configured")
            return False
        return True

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    BACKEND_API_URL = 'http://mock-api:5000/api'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name: Optional[str] = None) -> Config:
    """Get configuration based on environment"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    return config.get(config_name, config['default'])

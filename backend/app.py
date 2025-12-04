"""
Flask application for SRM API.
Main entry point for the backend server.
"""
import sys
from pathlib import Path

# Add parent directory to path to import from config and services
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask
from flask_cors import CORS
from routes.chat import chat_bp
from routes.ocr import ocr_bp
from routes.health import health_bp
from config.settings import settings


def create_app():
    """
    Create and configure Flask application.
    
    Returns:
        Flask: Configured Flask app instance
    """
    app = Flask(__name__)
    
    # CORS configuration - allow frontend to communicate
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000", "http://localhost:8501"],
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Configuration
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.config['JSON_AS_ASCII'] = False  # Support Arabic characters
    
    # Register blueprints
    app.register_blueprint(health_bp, url_prefix='/api')
    app.register_blueprint(chat_bp, url_prefix='/api')
    app.register_blueprint(ocr_bp, url_prefix='/api')
    
    return app


if __name__ == '__main__':
    # Validate configuration
    is_valid, errors = settings.validate()
    if not is_valid:
        print("❌ Configuration errors:")
        for error in errors:
            print(f"  - {error}")
        exit(1)
    
    print("✅ Configuration validated successfully")
    
    app = create_app()
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )

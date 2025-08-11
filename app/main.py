from flask import Flask
from flask_cors import CORS
import logging
import os

from app.config import Config
from app.database import init_db, create_tables
from app.routes import data_bp, forecast_bp, main_bp

def create_app():
    """Application factory function."""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(Config)
    
    # Enable CORS
    CORS(app)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize database
    init_db(app)
    
    # Register blueprints
    app.register_blueprint(data_bp)
    app.register_blueprint(forecast_bp)
    app.register_blueprint(main_bp)
    
    # Create tables within app context
    with app.app_context():
        create_tables()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=False)
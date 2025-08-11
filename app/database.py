from flask_sqlalchemy import SQLAlchemy
from flask import Flask

db = SQLAlchemy()

def init_db(app: Flask):
    """Initialize database with Flask app."""
    db.init_app(app)
    
def create_tables():
    """Create all database tables."""
    db.create_all()
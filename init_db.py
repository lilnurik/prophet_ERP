#!/usr/bin/env python3
"""
Database initialization script.
Creates all required tables in the PostgreSQL database.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.main import create_app
from app.database import create_tables

def init_database():
    """Initialize the database with all required tables."""
    print("Initializing database...")
    
    app = create_app()
    
    with app.app_context():
        try:
            create_tables()
            print("✅ Database tables created successfully!")
        except Exception as e:
            print(f"❌ Error creating database tables: {e}")
            sys.exit(1)

if __name__ == '__main__':
    init_database()
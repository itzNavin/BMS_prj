"""
Configuration settings for Bus Management System

Edit these settings to customize the application for your environment.
For production, change SECRET_KEY and set DEBUG = False.
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.absolute()

# Flask Configuration
# SECRET_KEY: Change this in production! Use a strong random key.
SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

# DEBUG: Set to False in production
DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'

# Database Configuration
# SQLite database (can be upgraded to PostgreSQL for production)
DATABASE_DIR = BASE_DIR / "database"
DATABASE_DIR.mkdir(exist_ok=True)
SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_DIR / "bus_management.db"}'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# Connection Pool Settings
# Optimized for real-time face recognition with multiple concurrent requests
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 20,        # Base connection pool size
    'max_overflow': 40,     # Maximum overflow connections
    'pool_timeout': 30,     # Timeout for getting connection (seconds)
    'pool_recycle': 3600,   # Recycle connections after 1 hour
    'pool_pre_ping': True   # Verify connections before using
}

# File Upload Configuration
UPLOAD_FOLDER = BASE_DIR / "uploads" / "students"
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
MAX_UPLOAD_SIZE = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'bmp'}

# Face Recognition Configuration
FACE_RECOGNITION_DB = BASE_DIR / "face_recognition_package" / "database"
FACE_RECOGNITION_CONFIG = BASE_DIR / "face_recognition_package" / "recognition_config.json"

# Session Configuration
SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
PERMANENT_SESSION_LIFETIME = 3600  # Session expires after 1 hour

# Application Configuration
APP_NAME = "Bus Management System"
VERSION = "1.0.0"

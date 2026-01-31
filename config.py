# config.py

import os
from datetime import timedelta

# Get the base directory (where app.py is located)
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # ==========================================
    # BASE CONFIGURATION
    # ==========================================
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    
    # ==========================================
    # DATABASE
    # ==========================================
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # ==========================================
    # FILE UPLOADS - Inside static folder for serving
    # ==========================================
    UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
    PROFILE_PICTURES_FOLDER = os.path.join(basedir, 'static', 'uploads', 'profile_pictures')
    LOGOS_FOLDER = os.path.join(basedir, 'static', 'uploads', 'logos')
    
    # Maximum file size (5MB)
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024
    
    # Allowed file extensions
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Image dimensions
    PROFILE_PICTURE_SIZE = (300, 300)  # Width x Height
    LOGO_SIZE = (400, 200)  # Width x Height
    
    # ==========================================
    # EMAIL
    # ==========================================
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USE_SSL = False
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


def init_upload_folders(app):
    """Create upload directories if they don't exist"""
    folders = [
        app.config.get('UPLOAD_FOLDER'),
        app.config.get('PROFILE_PICTURES_FOLDER'),
        app.config.get('LOGOS_FOLDER'),
    ]
    for folder in folders:
        if folder and not os.path.exists(folder):
            os.makedirs(folder)
            print(f"Created folder: {folder}")
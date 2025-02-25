import os

class Config:
    # Flask configuration
    DEBUG = os.environ.get('DEBUG', 'True') == 'True'
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    SECRET_KEY = os.environ.get('SECRET_KEY', 'development-key')
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Redis configuration
    REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', None)
    REDIS_DB = int(os.environ.get('REDIS_DB', 0))
    
    # Celery configuration
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}')
    
    # File storage configuration
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', './uploads')
    PROCESSED_FOLDER = os.environ.get('PROCESSED_FOLDER', './processed')
    RESULTS_FOLDER = os.environ.get('RESULTS_FOLDER', './results')
    
    # Base URL for generated URLs
    BASE_URL = os.environ.get('BASE_URL', 'http://localhost:5000')
    
    # Job configuration
    JOB_TIMEOUT = int(os.environ.get('JOB_TIMEOUT', 300))  # 5 minutes
    
    # Webhook configuration
    WEBHOOK_SECRET = os.environ.get('WEBHOOK_SECRET', '')
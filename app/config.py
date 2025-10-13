import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Secret Key for Sessions/CSRF
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///techhire.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Enable CSRF globally
    WTF_CSRF_ENABLED = False  # CSRF protection is enabled for form

    WTF_CSRF_EXEMPT_ROUTES = [  # List of API routes that are exempt from CSRF
        '/api/subscribe',
        '/api/unsubscribe',
        '/api/vapid-public-key',
    ]

    # VAPID Keys for Push Notifications
    VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY', '')
    VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY', '')
    VAPID_CLAIM_EMAIL = os.environ.get('VAPID_CLAIM_EMAIL', 'mailto:admin@example.com')

class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True


config = {
    'default': Config,
    'development': DevelopmentConfig,
    'production': ProductionConfig,
}
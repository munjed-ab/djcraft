from .base import *

DEBUG = True

SECRET_KEY = os.getenv('SECRET_KEY', 'dummy-secret-key-for-dev')

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Development-specific static/media settings

from .base import *

DEBUG = True
ALLOWED_HOSTS = ['*']

# Development database - SQLite for simplicity
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# CORS - allow all in development
CORS_ALLOW_ALL_ORIGINS = True

# Disable SMS in development - print code to console
SMS_BACKEND = 'console'

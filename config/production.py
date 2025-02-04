import os
from .settings import *

# Security settings
DEBUG = False
ALLOWED_HOSTS = [
    'dataconcierge-*-run.app',  # Cloud Run URLs
    os.getenv('ALLOWED_HOSTS', '').split(','),  # Custom domains
]

# Firestore settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',  # 使用SQLite作为Django的系统表存储
        'NAME': ':memory:',  # 使用内存数据库，因为我们主要使用Firestore
    }
}

# Firestore configuration
FIRESTORE_PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT', 'data-market-web')
FIRESTORE_COLLECTION_PREFIX = os.getenv('FIRESTORE_COLLECTION_PREFIX', 'dataconcierge')

# Static files
STATIC_URL = f"https://storage.googleapis.com/{os.getenv('GS_BUCKET_NAME')}/static/"
STATIC_ROOT = 'static'
STATICFILES_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'

# Media files
DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
GS_BUCKET_NAME = os.getenv('GS_BUCKET_NAME')
GS_DEFAULT_ACL = 'publicRead'

# Security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
} 
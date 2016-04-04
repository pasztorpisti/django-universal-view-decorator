import os

DEBUG = True

SECRET_KEY = 'TOP_SECRET'

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
    }
}

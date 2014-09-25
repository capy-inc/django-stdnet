import os
BASE_DIR = ''
from django.conf import settings
settings.configure(
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
            'TEST_NAME': os.path.join(BASE_DIR, 'test_db.sqlite3')
        }
    },
    STDNET_BACKENDS={
        'default': {
            'BACKEND': None
        }
    }
)

from .models import *
from .session import *
from .fields import *
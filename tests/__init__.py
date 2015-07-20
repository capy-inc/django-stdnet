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
    },
    MEDIA_ROOT='/tmp'
)

redis_server = None
redis_server_info = None


def setUpModule():
    import redis
    import testing.redis

    global redis_server
    global redis_server_info

    try:
        r = redis.Redis(host='redis')
        r.keys('*')
        redis_server_info = r.connection_pool.connection_kwargs
    except redis.connection.ConnectionError:
        redis_server = testing.redis.RedisServer()
        redis_server.start()
        redis_server_info = redis_server.dsn()


def tearDownModule():
    global redis_server

    if redis_server is not None:
        redis_server.stop()


from .models import *
from .session import *
from .fields import *
from .ttl import *
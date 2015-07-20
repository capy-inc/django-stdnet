from distutils.version import LooseVersion
import django
from django.test import TestCase

DJANGO_VERSION = LooseVersion(django.get_version())


class BaseTestCase(TestCase):
    app_label = 'test'

    def _setup_redis_db(self):
        from djangostdnet import models
        from djangostdnet import mapper
        from . import redis_server_info

        models.mapper = mapper.Mapper(default_backend='redis://%(host)s:%(port)d?db=%(db)d' % redis_server_info,
                                      install_global=True)

    def setUp(self):
        from django.core.management.color import no_style
        from django.db.models import loading

        self._setup_redis_db()

        self.seen_models = set()
        self.style = no_style()

        # HACK
        if LooseVersion('1.6') <= DJANGO_VERSION < LooseVersion('1.7'):
            pass
        elif LooseVersion('1.7') <= DJANGO_VERSION:
            from django.apps.config import AppConfig
            from django.utils.importlib import import_module
            self.app = AppConfig(self.app_label, import_module(__name__))
            loading.cache.ready = True
            loading.cache.set_installed_apps([self.app])
        else:
            raise NotImplementedError

    def _clear_registered_models(self):
        from django.db.models import loading

        # HACK
        if LooseVersion('1.6') <= DJANGO_VERSION < LooseVersion('1.7'):
            loading.cache.app_models.clear()
        elif LooseVersion('1.7') <= DJANGO_VERSION:
            loading.cache.unset_installed_apps()
            loading.cache.all_models.clear()
        else:
            raise NotImplementedError

    def _clear_redis_db(self):
        import redis
        from . import redis_server_info

        r = redis.from_url('redis://%(host)s:%(port)d?db=%(db)d' % redis_server_info)
        r.flushdb()

    def tearDown(self):
        self._clear_registered_models()
        self._clear_redis_db()

    def create_table_for_model(self, model):
        from django.db import connection

        sql = connection.creation.sql_create_model(model, self.style)[0]
        cursor = connection.cursor()
        for statement in sql:
            cursor.execute(statement)

    def register_manually(self, model):
        from django.db.models import loading

        loading.cache.register_model(self.app_label, model)

    def finish_defining_models(self):
        from django.db.models import loading

        if LooseVersion('1.7') <= DJANGO_VERSION:
            loading.cache.populate([self.app])

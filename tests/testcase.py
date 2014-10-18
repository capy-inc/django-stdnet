from django.test import TestCase


class BaseTestCase(TestCase):
    def setUp(self):
        from djangostdnet import models
        from djangostdnet import mapper
        models.mapper = mapper.Mapper(default_backend='redis://localhost:6379?db=0', install_global=True)

    def tearDown(self):
        from django.db.models import loading
        import redis

        # HACK to clear django model cache
        loading.cache.app_models.clear()
        r = redis.from_url('redis://localhost:6379?db=0')
        r.flushdb()

    def create_table_for_model(self, model):
        from django.db import models as dj_models
        from django.core.management.color import no_style

        connection = dj_models.connection
        sql = connection.creation.sql_create_model(model, no_style())[0][0]
        cursor = connection.cursor()
        cursor.execute(sql)

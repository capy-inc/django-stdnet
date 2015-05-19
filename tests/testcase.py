from django.test import TestCase


class BaseTestCase(TestCase):
    def setUp(self):
        from djangostdnet import models
        from djangostdnet import mapper
        from django.core.management.color import no_style

        models.mapper = mapper.Mapper(default_backend='redis://localhost:6379?db=0', install_global=True)
        self.seen_models = set()
        self.style = no_style()

    def tearDown(self):
        from django.db.models import loading
        import redis

        # HACK to clear django model cache
        loading.cache.app_models.clear()
        r = redis.from_url('redis://localhost:6379?db=0')
        r.flushdb()

    def create_tables(self):
        from django.db import models as dj_models

        connection = dj_models.connection
        pending_references = {}
        for model in dj_models.get_models(only_installed=False, include_auto_created=True):
            sql, references = connection.creation.sql_create_model(model, self.style, self.seen_models)
            self.seen_models.add(model)
            for refto, refs in references.items():
                pending_references.setdefault(refto, []).extend(refs)
                if refto in self.seen_models:
                    sql.extend(connection.creation.sql_for_pending_references(refto, self.style, pending_references))
            sql.extend(connection.creation.sql_for_pending_references(model, self.style, pending_references))
            cursor = connection.cursor()
            for statement in sql:
                cursor.execute(statement)

    def create_table_for_model(self, model):
        from django.db import models as dj_models

        connection = dj_models.connection
        sql = connection.creation.sql_create_model(model, self.style)[0]
        cursor = connection.cursor()
        for statement in sql:
            cursor.execute(statement)

from collections import Counter, defaultdict
from django.test import TestCase


class BaseTestCase(TestCase):
    def setUp(self):
        from stdnet import backends, odm
        from djangostdnet import models
        from djangostdnet import mapper
        from djangostdnet import fields

        class FakeBackendQuery(backends.BackendQuery):
            def _build(self, **kwargs):
                pass

            def _items(self, slic):
                return self.result

            def _execute_query(self):
                # simple support looking up by value
                if (len(self.queryelem) == 1
                    and list(self.queryelem)[0].lookup == 'value'):
                    name = self.queryelem.name
                    value = list(self.queryelem)[0].value
                    self.result = [obj for obj in self.backend.db[self.model].values()
                                   if getattr(obj, name) == value]
                    for obj in self.result:
                        obj.dbdata[self.model._meta.pkname()] = obj.pkvalue()
                        del obj.dbdata['state']
                    yield len(self.result)
                # and relation for OneToOneField test
                if (len(self.queryelem) == 1
                    and list(self.queryelem)[0].lookup == 'set'):
                    name = self.queryelem.name
                    for field in self.model._meta.fields:
                        if field.attname == name:
                            break
                    else:
                        raise ValueError("Attribute not found: %s", name)
                    # obtain related object's ids
                    rel_queryelem = list(self.queryelem)[0].value
                    rel_name = rel_queryelem.name
                    rel_value = list(rel_queryelem)[0].value
                    rel_result = [obj.pkvalue() for obj in self.backend.db[field.relmodel].values()
                                  if getattr(obj, rel_name) == rel_value]
                    # filter by the ids
                    self.result = [obj for obj in self.backend.db[self.model].values()
                                   if getattr(obj, name) in rel_result]
                    for obj in self.result:
                        obj.dbdata[self.model._meta.pkname()] = obj.pkvalue()
                        del obj.dbdata['state']
                    yield len(self.result)

        class FakeBackendDataServer(backends.BackendDataServer):
            Query = FakeBackendQuery

            def __init__(self):
                super(FakeBackendDataServer, self).__init__()
                self.db = defaultdict(dict)
                self.gen = Counter()

            def setup_connection(self, address):
                pass

            def execute_session(self, session_data):
                for session in session_data:
                    if session.dirty:
                        for obj in session.dirty:
                            for field in obj._meta.fields:
                                if isinstance(field, (odm.ForeignKey, fields.OneToOneField)):
                                    # reset field relation
                                    field_value = getattr(obj, '%s_id' % field.name)
                                    setattr(obj, field.name, None)
                                    setattr(obj, '%s_id' % field.name, field_value)
                            pk = obj.pkvalue()
                            if pk is None:
                                pk = current = self.gen[obj.__class__]
                                self.gen[obj.__class__] = current + 1
                                obj.pk().set_value(obj, current)
                            self.db[obj.__class__][pk] = obj
                    if session.deletes is not None:
                        for obj in session.deletes:
                            del self.db[obj.__class__][obj.pkvalue()]

        self.fake_backend = FakeBackendDataServer()
        models.mapper = mapper.Mapper(default_backend=self.fake_backend, install_global=True)

    def tearDown(self):
        from django.db.models import loading
        # HACK to clear django model cache
        loading.cache.app_models.clear()

    def create_table_for_model(self, model):
        from django.db import models as dj_models
        from django.core.management.color import no_style

        connection = dj_models.connection
        sql = connection.creation.sql_create_model(model, no_style())[0][0]
        cursor = connection.cursor()
        cursor.execute(sql)

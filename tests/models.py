import mock
from .testcase import BaseTestCase


class ConnectionSettingTestCase(BaseTestCase):
    def test_default(self):
        from stdnet import odm
        from djangostdnet import models

        class AModel(models.Model):
            name = odm.CharField()

            class Meta:
                register = False

        self.assertEqual(AModel.objects.backend.connection_string, models.mapper._default_backend)
        self.assertEqual(AModel.objects.read_backend.connection_string, models.mapper._default_backend)

    def test_meta_connection_string(self):
        from stdnet import odm
        from djangostdnet import models

        backend_url = 'redis://localhost:5555?db=1'
        read_backend_url = 'redis://localhost:5555?db=2'

        class AModel(models.Model):
            name = odm.CharField()

            class Meta:
                register = False
                backend = backend_url
                read_backend = read_backend_url

        self.assertEqual(AModel.objects.backend.connection_string, backend_url)
        self.assertEqual(AModel.objects.read_backend.connection_string, read_backend_url)

    def test_meta_connection_name_in_settings(self):
        from stdnet import odm
        from djangostdnet import models

        backend_url = 'redis://localhost:5555?db=1'
        read_backend_url = 'redis://localhost:5555?db=2'

        # specify same backend url for baackends
        with self.settings(STDNET_BACKENDS={'custom': backend_url}):
            class AModel(models.Model):
                name = odm.CharField()

                class Meta:
                    register = False
                    backend = 'custom'

            self.assertEqual(AModel.objects.backend.connection_string, backend_url)
            self.assertEqual(AModel.objects.read_backend.connection_string, backend_url)

            class AModel(models.Model):
                name = odm.CharField()

                class Meta:
                    register = False
                    backend = 'custom'
                    read_backend = 'custom'

            self.assertEqual(AModel.objects.backend.connection_string, backend_url)
            self.assertEqual(AModel.objects.read_backend.connection_string, backend_url)

        # specify individual backend url for each backend
        with self.settings(STDNET_BACKENDS={'custom': {'BACKEND': backend_url,
                                                       'READ_BACKEND': read_backend_url}}):
            class AModel(models.Model):
                name = odm.CharField()

                class Meta:
                    register = False
                    backend = 'custom'

            self.assertEqual(AModel.objects.backend.connection_string, backend_url)
            self.assertEqual(AModel.objects.read_backend.connection_string, read_backend_url)

            class AModel(models.Model):
                name = odm.CharField()

                class Meta:
                    register = False
                    backend = 'custom'
                    read_backend = 'custom'

            self.assertEqual(AModel.objects.backend.connection_string, backend_url)
            self.assertEqual(AModel.objects.read_backend.connection_string, read_backend_url)


    def test_vertical_sharding(self):
        from stdnet import odm
        from djangostdnet import models

        parent_backend_url = 'redis://localhost:5555?db=1'
        parent_read_backend_url = 'redis://localhost:5555?db=2'
        child_backend_url = 'redis://localhost:5555?db=3'
        child_read_backend_url = 'redis://localhost:5555?db=4'
        with self.settings(STDNET_BACKENDS={'parent': {'BACKEND': parent_backend_url,
                                                       'READ_BACKEND': parent_read_backend_url},
                                            'child': {'BACKEND': child_backend_url,
                                                      'READ_BACKEND': child_read_backend_url}}):

            class AParentModel(models.Model):
                name = odm.SymbolField()

                class Meta:
                    register = False
                    backend = 'parent'

            class AChildModel(models.Model):
                parent = odm.ForeignKey(AParentModel, unique=True)

                class Meta:
                    register = False
                    backend = 'child'

        self.assertEqual(AParentModel.objects.backend.connection_string, parent_backend_url)
        self.assertEqual(AParentModel.objects.read_backend.connection_string, parent_read_backend_url)
        self.assertEqual(AChildModel.objects.backend.connection_string, child_backend_url)
        self.assertEqual(AChildModel.objects.read_backend.connection_string, child_read_backend_url)


class ModelSaveTestCase(BaseTestCase):
    def test_save_new_instance_without_django_model(self):
        from djangostdnet import models
        from stdnet import odm

        class AModel(models.Model):
            name = odm.CharField()

            class Meta:
                register = False

        obj1 = AModel.objects.new(name='amodel1')
        obj2 = AModel.objects.new(name='amodel2')

        self.assertEqual([obj1.pkvalue(), obj2.pkvalue()],
                         [obj.pkvalue() for obj in AModel.objects.all()])
        self.assertEqual(obj1.name, 'amodel1')
        self.assertEqual(obj2.name, 'amodel2')

    def test_save_new_instance_from_django_stdnet_model(self):
        from django.db import models as dj_models
        from djangostdnet import models

        class ADjangoModel(dj_models.Model):
            name = dj_models.CharField(max_length=255)

        class AModel(models.Model):
            class Meta:
                django_model = ADjangoModel
                register = False

        self.create_table_for_model(ADjangoModel)

        obj1 = AModel.objects.new(name='amodel1')
        obj2 = AModel.objects.new(name='amodel2')
        dj_obj1 = ADjangoModel.objects.get(pk=obj1.id)
        dj_obj2 = ADjangoModel.objects.get(pk=obj2.id)

        self.assertEqual([dj_obj1.pk, dj_obj2.pk],
                         [dj_obj.pk for dj_obj in ADjangoModel.objects.all()])
        self.assertEqual([obj1.pkvalue(), obj2.pkvalue()],
                         [obj.pkvalue() for obj in AModel.objects.all()])
        self.assertEqual(dj_obj1.name, 'amodel1')
        self.assertEqual(dj_obj2.name, 'amodel2')

    def test_save_new_instance_from_django_model(self):
        from django.db import models as dj_models
        from djangostdnet import models

        class ADjangoModel(dj_models.Model):
            name = dj_models.CharField(max_length=255)

        class AModel(models.Model):
            class Meta:
                django_model = ADjangoModel
                register = False

        self.create_table_for_model(ADjangoModel)

        dj_obj1 = ADjangoModel(name='amodel')
        dj_obj1.save()
        self.assertIsNotNone(dj_obj1.pk)
        dj_obj_pk = dj_obj1.pk

        # In this case, there is no the object changes. So, Model.save() should not be called.
        def poison_save(self):
            raise AssertionError("die by poison")

        dj_obj1.save = poison_save.__get__(dj_obj1, ADjangoModel)

        # don't affect the django object
        obj1 = AModel.objects.new(id=dj_obj_pk, name=dj_obj1.name)

        self.assertEqual([obj1.pkvalue()],
                         [obj.pkvalue() for obj in AModel.objects.all()])
        self.assertEqual(obj1.id, dj_obj_pk)
        self.assertEqual(obj1.name, dj_obj1.name)

    def test_subscribe(self):
        from django.db import models as dj_models
        from djangostdnet import models

        class ADjangoModel(dj_models.Model):
            name = dj_models.CharField(max_length=255)

        class AModel(models.Model):
            class Meta:
                django_model = ADjangoModel
                register = False

        self.create_table_for_model(ADjangoModel)

        dj_obj = ADjangoModel(name='amodel')
        dj_obj.save()
        dj_obj_pk = dj_obj.pk

        obj = AModel.objects.get(id=dj_obj_pk)
        self.assertEqual(obj.name, 'amodel')

        dj_obj.name = 'yamodel'
        dj_obj.save()

        obj = AModel.objects.get(id=dj_obj_pk)
        self.assertEqual(obj.name, 'yamodel')

        dj_obj.delete()
        with self.assertRaises(AModel.DoesNotExist):
            AModel.objects.get(id=dj_obj_pk)

    def test_delete_from_django_stdnet_model(self):
        from django.db import models as dj_models
        from djangostdnet import models

        class ADjangoModel(dj_models.Model):
            name = dj_models.CharField(max_length=255)

        class AModel(models.Model):
            class Meta:
                django_model = ADjangoModel
                register = False

        self.create_table_for_model(ADjangoModel)

        dj_obj = ADjangoModel(name='amodel')
        dj_obj.save()
        dj_obj_pk = dj_obj.pk

        obj = AModel.objects.get(id=dj_obj_pk)
        obj.delete()

        with self.assertRaises(ADjangoModel.DoesNotExist):
            ADjangoModel.objects.get(pk=dj_obj_pk)

    def test_delete_from_django_model(self):
        from django.db import models as dj_models
        from djangostdnet import models

        class ADjangoModel(dj_models.Model):
            name = dj_models.CharField(max_length=255)

        class AModel(models.Model):
            class Meta:
                django_model = ADjangoModel
                register = False

        self.create_table_for_model(ADjangoModel)

        dj_obj = ADjangoModel(name='amodel')
        dj_obj.save()
        dj_obj_pk = dj_obj.pk

        AModel.objects.get(id=dj_obj_pk)
        dj_obj.delete()

        with self.assertRaises(AModel.DoesNotExist):
            AModel.objects.get(id=dj_obj_pk)


class ModelExtendTestCase(BaseTestCase):
    def test_it(self):
        from django.db import models as dj_models
        from djangostdnet import models
        from stdnet import odm

        class ADjangoModel(dj_models.Model):
            name = dj_models.CharField(max_length=255)

        class AModel(models.Model):
            status = odm.IntegerField()

            @property
            def next_status(self):
                return self.status + 1

            class Meta:
                django_model = ADjangoModel
                register = False

        self.assertTrue(isinstance(AModel._meta.dfields['name'], odm.CharField))
        self.assertTrue(isinstance(AModel._meta.dfields['status'], odm.IntegerField))

        self.create_table_for_model(ADjangoModel)

        obj = AModel.objects.new(name='amodel', status=3)
        obj = AModel.objects.get(id=obj.id)
        dj_obj = ADjangoModel.objects.get(pk=obj.id)

        self.assertEqual(obj.name, dj_obj.name)
        self.assertFalse(hasattr(dj_obj, 'status'))
        self.assertIn(obj, AModel.objects.all())
        self.assertEqual(obj.name, 'amodel')
        self.assertEqual(obj.status, 3)
        self.assertEqual(obj.next_status, 4)


class CustomFieldTestCase(BaseTestCase):
    def logger_warn_called(self, cls):
        return mock.call(
            'not supported for field type: %s',
            cls.__name__)

    def test_register(self):
        from django.db import models as dj_models
        from djangostdnet import models
        from stdnet import odm

        class AField(dj_models.IntegerField):
            pass

        class ADjangoModel(dj_models.Model):
            status = AField()

        _mapping = dict(models._mapping)
        with mock.patch('djangostdnet.models._mapping', _mapping):
            models.register_field_mapping(AField, odm.IntegerField)

            with mock.patch('djangostdnet.models.logger') as logger:
                class AModel(models.Model):
                    class Meta:
                        django_model = ADjangoModel
                        register = False

                self.assertNotIn(self.logger_warn_called(AField),
                                 logger.warn.call_args_list)
        self.assertIn('status', AModel._meta.dfields)

    def test_not_support(self):
        from django.db import models as dj_models
        from djangostdnet import models

        class AField(dj_models.IntegerField):
            pass

        class ADjangoModel(dj_models.Model):
            status = AField()

        with mock.patch('djangostdnet.models.logger') as logger:
            class AModel(models.Model):
                class Meta:
                    django_model = ADjangoModel
                    register = False

            self.assertIn(self.logger_warn_called(AField),
                          logger.warn.call_args_list)
        self.assertNotIn('status', AModel._meta.dfields)


class ProxyModelTestCase(BaseTestCase):
    def test_it(self):
        from django.db import models as dj_models
        from djangostdnet import models

        class AParentDjangoModel(dj_models.Model):
            name = dj_models.CharField(max_length=10)

            @property
            def emphasized_name(self):
                return '** %s **' % self.name

            def hi(self, name):
                return 'hi %s, I\'m %s' % (name, self.name)

            class Meta:
                abstract = True

        class AChildDjangoModel(AParentDjangoModel):
            def bye(self, name):
                return 'bye %s' % name

        class AModel(models.Model):
            class Meta:
                django_model = AChildDjangoModel

        self.create_table_for_model(AChildDjangoModel)

        obj = AModel.objects.new(name='foo')
        self.assertEqual(obj.emphasized_name, '** foo **')
        self.assertEqual(obj.hi('bar'), 'hi bar, I\'m foo')
        self.assertEqual(obj.bye('bar'), 'bye bar')


class AnotherTypePrimaryKeyModelTestCase(BaseTestCase):
    def test_from_django_model(self):
        from django.db import models as dj_models
        from djangostdnet import models

        class ADjangoModel(dj_models.Model):
            name = dj_models.CharField(max_length=10, primary_key=True)

        class AModel(models.Model):
            class Meta:
                django_model = ADjangoModel
                register = False

        self.create_table_for_model(ADjangoModel)

        dj_obj = ADjangoModel.objects.create(name='foo')
        obj = AModel.objects.get(name=dj_obj.name)
        self.assertEqual(obj.name, 'foo')

    def test_from_stdnet_model(self):
        from django.db import models as dj_models
        from djangostdnet import models

        class ADjangoModel(dj_models.Model):
            name = dj_models.CharField(max_length=10, primary_key=True)

        class AModel(models.Model):
            class Meta:
                django_model = ADjangoModel
                register = False

        self.create_table_for_model(ADjangoModel)

        obj = AModel.objects.new(name='foo')
        dj_obj = ADjangoModel.objects.get(name=obj.name)
        self.assertEqual(dj_obj.name, 'foo')

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

        self.assertEqual(AModel.objects.backend, models.mapper._default_backend)
        self.assertEqual(AModel.objects.read_backend, models.mapper._default_backend)

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

        # specify backend url as both
        with self.settings(STDNET_BACKENDS={'custom': backend_url}):
            class AModel(models.Model):
                name = odm.CharField()

                class Meta:
                    register = False
                    backend = 'custom'
                    read_backend = 'custom'

        self.assertEqual(AModel.objects.backend.connection_string, backend_url)
        self.assertEqual(AModel.objects.read_backend.connection_string, backend_url)

        # specify backend and read_backend url
        with self.settings(STDNET_BACKENDS={'custom': {'BACKEND': backend_url,
                                                       'READ_BACKEND': read_backend_url}}):
            class AModel(models.Model):
                name = odm.CharField()

                class Meta:
                    register = False
                    backend = 'custom'
                    read_backend = 'custom'

        self.assertEqual(AModel.objects.backend.connection_string, backend_url)
        self.assertEqual(AModel.objects.read_backend.connection_string, read_backend_url)


class ModelSaveTestCase(BaseTestCase):
    def test_save_new_instance_without_django_model(self):
        from djangostdnet import models
        from stdnet import odm

        class AModel(models.Model):
            name = odm.CharField()

            class Meta:
                register = False

        obj = AModel.objects.new(name='amodel')

        self.assertIn(obj, self.fake_backend.db[AModel].values())
        self.assertEqual(obj.name, 'amodel')

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

        obj = AModel.objects.new(name='amodel')

        self.assertEqual([obj], self.fake_backend.db[AModel].values())
        self.assertEqual(obj.id, obj._instance.id)
        self.assertEqual(obj.name, obj._instance.name)
        self.assertEqual(obj.name, 'amodel')

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

        dj_obj = ADjangoModel(name='amodel')
        dj_obj.save()
        self.assertIsNotNone(dj_obj.pk)
        dj_obj_pk = dj_obj.pk

        # In this case, there is no model changes. So, Model.save() should not be called.
        def poison_save(self):
            raise AssertionError("die by poison")

        dj_obj.save = poison_save.__get__(dj_obj, ADjangoModel)

        # don't affect the django object
        obj = AModel.objects.new(id=dj_obj_pk, name=dj_obj.name)

        self.assertIn(obj, self.fake_backend.db[AModel].values())
        self.assertEqual(obj._instance.id, dj_obj_pk)
        self.assertEqual(obj.id, obj._instance.id)
        self.assertEqual(obj.name, obj._instance.name)
        self.assertEqual(obj.name, 'amodel')

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

        self.assertIn(obj, self.fake_backend.db[AModel].values())
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

from .testcase import BaseTestCase


class SessionTestCase(BaseTestCase):
    def test_delete_quietly_when_stdnet_model_none(self):
        """possible case of redis-out"""
        import redis
        from django.db import models as dj_models
        from djangostdnet import models

        class ADjangoModel(dj_models.Model):
            name = dj_models.CharField(max_length=255)

        class AModel(models.Model):
            class Meta:
                django_model = ADjangoModel
                register = False

        self.create_table_for_model(ADjangoModel)

        obj = ADjangoModel.objects.create(name='obj1')

        # simulate lacking of object correspond to the obj as redis-out
        r = redis.from_url(models.mapper._default_backend)
        r.flushdb()

        AModel.objects.session().delete_from_django_object(AModel.objects, obj)
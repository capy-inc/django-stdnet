from .testcase import BaseTestCase


class SessionTestCase(BaseTestCase):
    def test_delete_quietly_when_stdnet_model_none(self):
        """possible case of redis-out"""
        from django.db import models as dj_models
        from djangostdnet import models

        class SessionDeleteQuietlyWhenStdnetModelNoneModel(dj_models.Model):
            name = dj_models.CharField(max_length=255)

        class AModel(models.Model):
            class Meta:
                django_model = SessionDeleteQuietlyWhenStdnetModelNoneModel
                register = False

        self.create_table_for_model(SessionDeleteQuietlyWhenStdnetModelNoneModel)

        obj = SessionDeleteQuietlyWhenStdnetModelNoneModel.objects.create(name='obj1')

        # simulate lacking of object correspond to the obj as redis-out
        del self.fake_backend.db[AModel][obj.pk]

        AModel.objects.session().delete_from_django_object(AModel.objects, obj)
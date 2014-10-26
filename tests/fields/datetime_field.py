from ..testcase import BaseTestCase


class DateTimeFieldTestCase(BaseTestCase):
    def test_auto_now(self):
        from datetime import datetime
        from djangostdnet import models

        class AModel(models.Model):
            updated = models.DateTimeField(auto_now=True)

            class Meta:
                register = False

        obj = AModel.objects.new()
        obj = AModel.objects.get(id=obj.id)
        self.assertTrue(isinstance(obj.updated, datetime))

    def test_auto_now_add(self):
        from datetime import datetime
        from djangostdnet import models

        class AModel(models.Model):
            updated = models.DateTimeField(auto_now=True)
            created = models.DateTimeField(auto_now_add=True)

            class Meta:
                register = False

        obj = AModel.objects.new()
        obj = AModel.objects.get(id=obj.id)
        self.assertTrue(isinstance(obj.updated, datetime))
        self.assertEqual(obj.created, obj.updated)

        obj.save()
        obj = AModel.objects.get(id=obj.id)
        self.assertTrue(obj.created < obj.updated)
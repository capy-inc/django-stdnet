from freezegun import freeze_time
from .testcase import BaseTestCase


class TTLTestCase(BaseTestCase):
    def test_it(self):
        from stdnet import odm
        from djangostdnet import models, ttl as ttl_mod

        class AModel(models.Model):
            name = odm.CharField()
            ttl = ttl_mod.TTLField()

            manager_class = ttl_mod.TTLManager

        # must not be raise ObjectDoesNotExist when ttl is positive
        obj = AModel.objects.new(name='foo', ttl=10)
        AModel.objects.get(id=obj.id)

        obj = AModel.objects.new(name='foo', ttl=-1)
        with self.assertRaises(AModel.DoesNotExist):
            AModel.objects.get(id=obj.id)

        with freeze_time('1970-01-01'):
            obj = AModel.objects.new(name='foo', ttl=10)
        with self.assertRaises(AModel.DoesNotExist):
            AModel.objects.get(id=obj.id)

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

            class Meta:
                register = False

        obj = AModel.objects.new(name='foo', ttl=None)
        self.assertEqual(AModel.objects.get(id=obj.id).ttl, None,
                         "Must not raise ObjectDoesNotExist if TTL is not set")

        obj = AModel.objects.new(name='foo', ttl=10)
        self.assertEqual(AModel.objects.get(id=obj.id).ttl, 10,
                         "Must not raise ObjectDoesNotExist if TTL is effective")

        obj = AModel.objects.new(name='foo', ttl=-1)
        with self.assertRaises(AModel.DoesNotExist,
                               msg="Must raise ObjectDoesNotExist if TTL is expired"):
            AModel.objects.get(id=obj.id)

        with freeze_time('1970-01-01'):
            obj = AModel.objects.new(name='foo', ttl=10)
        with self.assertRaises(AModel.DoesNotExist,
                               msg="Even TTL value is positive, "
                               "Must raise ObjectDoesNotExist if its expired"):
            AModel.objects.get(id=obj.id)

    def _make_simple_ttl_instances(self):
        from stdnet import odm
        from djangostdnet import models, ttl as ttl_mod

        class AModel(models.Model):
            name = odm.CharField()
            ttl = ttl_mod.TTLField()

            manager_class = ttl_mod.TTLManager

            class Meta:
                register = False

        # instances with enough ttl
        AModel.objects.new(name='foo1', ttl=100)
        with freeze_time('1970-01-01'):
            AModel.objects.new(name='foo2', ttl=100)
        AModel.objects.new(name='foo3', ttl=100)
        with freeze_time('1970-01-01'):
            AModel.objects.new(name='foo4', ttl=100)
        AModel.objects.new(name='foo5', ttl=100)
        return AModel.objects

    def test_slice_index(self):
        """
        When a object allocated at the index is expired, retrieves valid successor in index access.
        Caveat When accessing a object allocated at the index is valid, will skip the expired predecessors.
        """
        objects = self._make_simple_ttl_instances()
        obj = objects.query()[1]
        self.assertEqual(obj.name, 'foo3')
        obj = objects.query()[1]
        self.assertEqual(obj.name, 'foo3')
        obj = objects.query()[3]
        self.assertEqual(obj.name, 'foo5')
        obj = objects.query()[2]
        self.assertEqual(obj.name, 'foo5')
        with self.assertRaises(IndexError):
            objects.query()[3]

    # These slice behavior may be changed in the future.
    def test_slice_start(self):
        objects = self._make_simple_ttl_instances()
        # drop foo2 and foo4
        self.assertEqual([obj.name for obj in objects.query()[1:]],
                         ['foo3', 'foo5'])

    def test_slice_stop(self):
        objects = self._make_simple_ttl_instances()
        # drop foo2
        self.assertEqual([obj.name for obj in objects.query()[:1]],
                         ['foo1'])

    def test_slice_start_stop(self):
        objects = self._make_simple_ttl_instances()
        # drop foo2 and foo4
        self.assertEqual([obj.name for obj in objects.query()[1:3]],
                         ['foo3'])

from ..testcase import BaseTestCase


class ManyToManyTestCase(BaseTestCase):
    def setUp(self):
        super(ManyToManyTestCase, self).setUp()

        from django.db import models as dj_models
        from djangostdnet import models

        class DjangoModelA(dj_models.Model):
            name = dj_models.CharField(max_length=255)

        class DjangoModelB(dj_models.Model):
            neighbors = dj_models.ManyToManyField(DjangoModelA)

        class ModelA(models.Model):
            class Meta:
                django_model = DjangoModelA

        class ModelB(models.Model):
            class Meta:
                django_model = DjangoModelB

        self.create_tables()

        self.dj_model_a = DjangoModelA
        self.dj_model_b = DjangoModelB
        self.std_model_a = ModelA
        self.std_model_b = ModelB

    def test_many_to_many(self):
        dj_obj = self.dj_model_a.objects.create(name='foo')
        neighbor = self.dj_model_b.objects.create()
        neighbor.neighbors.add(dj_obj)

        self.assertTrue(dj_obj.djangomodelb_set.get().neighbors.get() == dj_obj, "Cyclic Check of Relation on Django")

        obj = self.std_model_a.objects.get()
        self.skipTest("Doesn't support translated ManyToManyRelation at all")
        self.assertTrue(obj.modelb_set.get().neighbors.get() == obj, "Cyclic Check of Relation on Stdnet")

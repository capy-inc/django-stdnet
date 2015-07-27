from ..testcase import BaseTestCase


class BasicManyToManyTestCase(BaseTestCase):
    def setUp(self):
        super(BasicManyToManyTestCase, self).setUp()

        from django.db import models as dj_models
        from djangostdnet import models

        class DjangoModelA(dj_models.Model):
            name = dj_models.CharField(max_length=255)

            class Meta:
                app_label = self.app_label

        class DjangoModelB(dj_models.Model):
            neighbors = dj_models.ManyToManyField(DjangoModelA)

            class Meta:
                app_label = self.app_label

        class ModelA(models.Model):
            class Meta:
                django_model = DjangoModelA

        class ModelB(models.Model):
            class Meta:
                django_model = DjangoModelB

        self.finish_defining_models()
        self.create_table_for_model(DjangoModelA)
        self.create_table_for_model(DjangoModelB)
        for field in DjangoModelB._meta.many_to_many:
            self.create_table_for_model(field.rel.through)

        self.dj_model_a = DjangoModelA
        self.dj_model_b = DjangoModelB
        self.std_model_a = ModelA
        self.std_model_b = ModelB

    def test_save_from_django(self):
        dj_obj = self.dj_model_a.objects.create(name='foo')
        neighbor = self.dj_model_b.objects.create()
        neighbor.neighbors.add(dj_obj)

        computed_neighbor = dj_obj.djangomodelb_set.get()
        self.assertEquals(neighbor, computed_neighbor, "Cyclic Check of Relation on Django")
        self.assertEquals(computed_neighbor.neighbors.get(), dj_obj, "Cyclic Check of Relation on Django")

        obj = self.std_model_a.objects.get()
        neighbor_std = self.std_model_b.objects.get()

        computed_neighbor_std = obj.modelb_set.get()
        self.assertEquals(neighbor_std, computed_neighbor_std, "Cyclic Check of Relation on Stdnet")
        self.assertEquals(computed_neighbor_std.neighbors.get(), obj, "Cyclic Check of Relation on Stdnet")

        neighbor.neighbors.remove(dj_obj)
        self.assertEquals(len(obj.modelb_set.all()), 0)
        self.assertEquals(len(neighbor_std.neighbors.all()), 0)

    def test_save_from_stdnet(self):
        std_obj = self.std_model_a.objects.new(name='foo')
        neighbor = self.std_model_b.objects.new()
        neighbor.neighbors.add(std_obj)

        computed_neighbor = std_obj.modelb_set.get()
        self.assertEquals(neighbor, computed_neighbor, "Cyclic Check of Relation on Stdnet")
        self.assertEquals(computed_neighbor.neighbors.get(), std_obj, "Cyclic Check of Relation on Stdnet")

        dj_obj = self.dj_model_a.objects.get()
        dj_neighbor = self.dj_model_b.objects.get()

        dj_computed_neighbor = dj_obj.djangomodelb_set.get()
        self.assertEquals(dj_neighbor, dj_computed_neighbor, "Cyclic Check of Relation on Django")
        self.assertEquals(dj_computed_neighbor.neighbors.get(), dj_obj, "Cyclic Check of Relation on Django")

        neighbor.neighbors.remove(std_obj)
        self.assertEquals(len(dj_obj.djangomodelb_set.all()), 0)
        self.assertEquals(len(dj_neighbor.neighbors.all()), 0)


class SpecifiedRelatedNameTest(BaseTestCase):
    def setUp(self):
        super(SpecifiedRelatedNameTest, self).setUp()

        from django.db import models as dj_models
        from djangostdnet import models

        class DjangoModelA(dj_models.Model):
            name = dj_models.CharField(max_length=255)

            class Meta:
                app_label = self.app_label

        class DjangoModelTag(dj_models.Model):
            name = dj_models.CharField(max_length=255)
            targets = dj_models.ManyToManyField(DjangoModelA, related_name='tags')

            class Meta:
                app_label = self.app_label

        class ModelA(models.Model):
            class Meta:
                django_model = DjangoModelA

        class ModelTag(models.Model):
            class Meta:
                django_model = DjangoModelTag

        self.finish_defining_models()
        self.create_table_for_model(DjangoModelA)
        self.create_table_for_model(DjangoModelTag)
        for field in DjangoModelTag._meta.many_to_many:
            self.create_table_for_model(field.rel.through)

        self.dj_model_a = DjangoModelA
        self.dj_model_tag = DjangoModelTag
        self.std_model_a = ModelA
        self.std_model_tag = ModelTag

    def test_it(self):
        obj = self.std_model_a.objects.new(name='foo')
        tag = self.std_model_tag.objects.new(name='foo')

        tag.targets.add(obj)

        assert {obj} == set(tag.targets.query())
        assert {tag} == set(obj.tags.query())

        dj_obj = self.dj_model_a.objects.get(id=obj.id)
        dj_tag = self.dj_model_tag.objects.get(id=tag.id)

        assert {dj_obj} == set(dj_tag.targets.all())
        assert {dj_tag} == set(dj_obj.tags.all())


class RelationCheckTest(BaseTestCase):
    def setUp(self):
        super(RelationCheckTest, self).setUp()

        from django.db import models as dj_models
        from djangostdnet import models

        class DjangoModelA(dj_models.Model):
            name = dj_models.CharField(max_length=255)

            class Meta:
                app_label = self.app_label

        class DjangoModelTag(dj_models.Model):
            name = dj_models.CharField(max_length=255)
            targets = dj_models.ManyToManyField(DjangoModelA)

            class Meta:
                app_label = self.app_label

        class ModelA(models.Model):
            class Meta:
                django_model = DjangoModelA

        class ModelTag(models.Model):
            class Meta:
                django_model = DjangoModelTag

        self.finish_defining_models()
        self.create_table_for_model(DjangoModelA)
        self.create_table_for_model(DjangoModelTag)
        for field in DjangoModelTag._meta.many_to_many:
            self.create_table_for_model(field.rel.through)

        self.dj_model_a = DjangoModelA
        self.dj_model_tag = DjangoModelTag
        self.std_model_a = ModelA
        self.std_model_tag = ModelTag

    def test_it(self):
        obj_foo = self.std_model_a.objects.new(name='foo')
        obj_bar = self.std_model_a.objects.new(name='bar')
        obj_baz = self.std_model_a.objects.new(name='baz')

        tag_foo = self.std_model_tag.objects.new(name='foo')
        tag_bar = self.std_model_tag.objects.new(name='bar')
        tag_baz = self.std_model_tag.objects.new(name='baz')

        tag_foo.targets.add(obj_foo)
        tag_foo.targets.add(obj_bar)
        tag_bar.targets.add(obj_bar)
        tag_baz.targets.add(obj_baz)

        assert {obj_foo, obj_bar} == set(tag_foo.targets.query())
        assert {obj_bar} == set(tag_bar.targets.query())
        assert {obj_baz} == set(tag_baz.targets.query())
        assert {tag_foo} == set(obj_foo.modeltag_set.query())
        assert {tag_foo, tag_bar} == set(obj_bar.modeltag_set.query())
        assert {tag_baz} == set(obj_baz.modeltag_set.query())

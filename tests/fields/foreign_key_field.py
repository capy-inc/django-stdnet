from ..testcase import BaseTestCase


class ForeignKeyFieldTestCase(BaseTestCase):
    def test_foreign_key(self):
        from django.db import models as dj_models
        from djangostdnet import models

        class ADjangoParentModel(dj_models.Model):
            name = dj_models.CharField(max_length=255)

        class ADjangoChildModel(dj_models.Model):
            parent = dj_models.ForeignKey(ADjangoParentModel)

        class AParentModel(models.Model):
            class Meta:
                django_model = ADjangoParentModel

        class AChildModel(models.Model):
            class Meta:
                django_model = ADjangoChildModel

        self.create_table_for_model(ADjangoParentModel)
        self.create_table_for_model(ADjangoChildModel)

        # create stdnet relation, create django relation implicitly
        parent_obj1 = AParentModel.objects.new(name='parent1')
        child_obj1 = AChildModel.objects.new(parent=parent_obj1)
        self.assertEqual(child_obj1.parent, parent_obj1)
        # auto generated related name of django and stdnet are diverged.
        # recommend set related_name manually.
        self.assertIn(child_obj1, list(parent_obj1.achildmodel_parent_set.all()))

        parent_dj_obj1 = ADjangoParentModel.objects.get(pk=parent_obj1.pkvalue())
        child_dj_obj1 = ADjangoChildModel.objects.get(pk=child_obj1.pkvalue())
        self.assertEqual(child_dj_obj1.parent, parent_dj_obj1)
        self.assertIn(child_dj_obj1, list(parent_dj_obj1.adjangochildmodel_set.all()))

        parent_obj2 = AParentModel.objects.new(name='parent2')
        child_obj1.parent = parent_obj2
        child_obj1.save()

        parent_dj_obj2 = ADjangoParentModel.objects.get(pk=parent_obj2.pkvalue())
        child_dj_obj1 = ADjangoChildModel.objects.get(pk=child_obj1.pkvalue())
        self.assertEqual(child_dj_obj1.parent, parent_dj_obj2)
        self.assertIn(child_dj_obj1, list(parent_dj_obj2.adjangochildmodel_set.all()))

        # create django relation, create stdnet relation implicitly
        parent_dj_obj3 = ADjangoParentModel.objects.create(name='parent3')
        child_dj_obj3 = ADjangoChildModel.objects.create(parent=parent_dj_obj3)

        parent_obj3 = AParentModel.objects.get(id=parent_dj_obj3.pk)
        child_obj3 = AChildModel.objects.get(id=child_dj_obj3.pk)
        self.assertEqual(child_obj3.parent, parent_obj3)
        self.assertIn(child_obj3, list(parent_obj3.achildmodel_parent_set.all()))

        parent_dj_obj4 = ADjangoParentModel.objects.create(name='parent4')
        child_dj_obj3.parent = parent_dj_obj4
        child_dj_obj3.save()

        parent_obj4 = AParentModel.objects.get(id=parent_dj_obj4.pk)
        child_obj3 = AChildModel.objects.get(id=child_dj_obj3.pk)
        self.assertEqual(child_obj3.parent, parent_obj4)
        self.assertIn(child_obj3, list(parent_obj4.achildmodel_parent_set.all()))


class QuerySetDeletionTestCase(BaseTestCase):
    """
    Checking for relation with unique

    This is because of https://github.com/lsbardel/python-stdnet/pull/82
    """
    def test_it(self):
        from djangostdnet import models
        from stdnet import odm

        class ParentModel(odm.StdModel):
            name = odm.SymbolField()

            class Meta:
                register = False

        class ChildModel(odm.StdModel):
            parent = odm.ForeignKey(ParentModel, unique=True)

            class Meta:
                register = False

        models = odm.Router(models.mapper._default_backend)
        models.register(ParentModel)
        models.register(ChildModel)

        parent_obj1 = models[ParentModel].new(name='parent1')
        parent_obj2 = models[ParentModel].new(name='parent2')
        parent_obj3 = models[ParentModel].new(name='parent3')
        child_obj1 = models[ChildModel].new(parent=parent_obj1)
        child_obj2 = models[ChildModel].new(parent=parent_obj2)
        child_obj3 = models[ChildModel].new(parent=parent_obj3)

        self.assertEqual(models[ParentModel].query().all(), [parent_obj1, parent_obj2, parent_obj3])
        self.assertEqual(models[ChildModel].query().all(), [child_obj1, child_obj2, child_obj3])

        self.assertEqual(
            models[ChildModel].query().filter(
                parent=models[ParentModel].query().filter(name='parent2')).all(),
            [child_obj2])
        self.assertEqual(
            models[ChildModel].query().filter(
                parent=models[ParentModel].query().filter(name=('parent1', 'parent3'))).all(),
            [child_obj1, child_obj3])

        # This is the checking
        models[ChildModel].query().filter(
            parent=models[ParentModel].query().filter(name='parent2')).delete()

        self.assertEqual(models[ParentModel].query().all(), [parent_obj1, parent_obj2, parent_obj3])
        self.assertEqual(models[ChildModel].query().all(), [child_obj1, child_obj3])

        self.assertEqual(parent_obj1.childmodel_parent_set.all(), [child_obj1])
        self.assertEqual(parent_obj2.childmodel_parent_set.all(), [])
        self.assertEqual(parent_obj3.childmodel_parent_set.all(), [child_obj3])

        # After that, another must still work
        child_obj3.parent = parent_obj2
        child_obj3.save()

        self.assertEqual(models[ParentModel].query().all(), [parent_obj1, parent_obj2, parent_obj3])
        self.assertEqual(models[ChildModel].query().all(), [child_obj1, child_obj3])

        self.assertEqual(parent_obj1.childmodel_parent_set.all(), [child_obj1])
        self.assertEqual(parent_obj2.childmodel_parent_set.all(), [child_obj3])
        self.assertEqual(parent_obj3.childmodel_parent_set.all(), [])

        parent_obj2.delete()

        self.assertEqual(models[ParentModel].query().all(), [parent_obj1, parent_obj3])
        self.assertEqual(models[ChildModel].query().all(), [child_obj1])

        self.assertEqual(parent_obj1.childmodel_parent_set.all(), [child_obj1])
        self.assertEqual(parent_obj3.childmodel_parent_set.all(), [])

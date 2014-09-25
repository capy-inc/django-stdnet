from .testcase import BaseTestCase


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


class OneToOneFieldTestCase(BaseTestCase):
    def test_model_relation(self):
        from django.db import models as dj_models
        from djangostdnet import models

        class ADjangoParentModel(dj_models.Model):
            name = dj_models.CharField(max_length=255)

        class ADjangoChildModel(dj_models.Model):
            parent = dj_models.OneToOneField(ADjangoParentModel)

        class AParentModel(models.Model):
            class Meta:
                django_model = ADjangoParentModel
                register = False

        class AChildModel(models.Model):
            class Meta:
                django_model = ADjangoChildModel
                register = False

        self.create_table_for_model(ADjangoParentModel)
        self.create_table_for_model(ADjangoChildModel)

        # create stdnet relation, create django relation implicitly
        parent_obj1 = AParentModel.objects.new(name='parent1')
        child_obj1 = AChildModel.objects.new(parent=parent_obj1)
        self.assertEqual(child_obj1.parent, parent_obj1)
        self.assertEqual(child_obj1, parent_obj1.achildmodel_parent)

        parent_dj_obj1 = ADjangoParentModel.objects.get(pk=parent_obj1.pkvalue())
        child_dj_obj1 = ADjangoChildModel.objects.get(pk=child_obj1.pkvalue())
        self.assertEqual(child_dj_obj1.parent, parent_dj_obj1)

        # change parent
        parent_obj2 = AParentModel.objects.new(name='parent2')
        child_obj1.parent = parent_obj2
        child_obj1.save()

        parent_dj_obj2 = ADjangoParentModel.objects.get(pk=parent_obj2.pkvalue())
        child_dj_obj1 = ADjangoChildModel.objects.get(pk=child_obj1.pkvalue())
        self.assertEqual(child_dj_obj1.parent, parent_dj_obj2)

        # change child
        parent_obj1.achildmodel_parent = child_obj1
        parent_obj1.achildmodel_parent.save()
        parent_dj_obj1 = ADjangoParentModel.objects.get(pk=parent_obj1.pkvalue())
        child_dj_obj1 = ADjangoChildModel.objects.get(pk=child_obj1.pkvalue())
        self.assertEqual(child_dj_obj1, parent_dj_obj1.adjangochildmodel)

        # create django relation, create stdnet relation implicitly
        parent_dj_obj3 = ADjangoParentModel.objects.create(name='parent3')
        child_dj_obj3 = ADjangoChildModel.objects.create(parent=parent_dj_obj3)

        parent_obj3 = AParentModel.objects.get(id=parent_dj_obj3.pk)
        child_obj3 = AChildModel.objects.get(id=child_dj_obj3.pk)
        self.assertEqual(child_obj3.parent, parent_obj3)
        self.assertEqual(child_obj3, parent_obj3.achildmodel_parent)

        # change parent
        parent_dj_obj4 = ADjangoParentModel.objects.create(name='parent4')
        child_dj_obj3.parent = parent_dj_obj4
        child_dj_obj3.save()

        parent_obj4 = AParentModel.objects.get(id=parent_dj_obj4.pk)
        child_obj3 = AChildModel.objects.get(id=child_dj_obj3.pk)
        self.assertEqual(child_obj3.parent, parent_obj4)
        self.assertEqual(child_obj3, parent_obj4.achildmodel_parent)

        # change child
        parent_dj_obj3.adjangochildmodel = child_dj_obj3
        parent_dj_obj3.adjangochildmodel.save()
        parent_obj3 = AParentModel.objects.get(id=parent_dj_obj3.pk)
        child_obj3 = AChildModel.objects.get(id=child_dj_obj3.pk)
        self.assertEqual(child_obj3, parent_obj3.achildmodel_parent)

    def test_filter(self):
        from stdnet import odm
        from djangostdnet import models

        class AParentModel(models.Model):
            name = odm.SymbolField()

            class Meta:
                register = False

        class AChildModel(models.Model):
            parent = models.OneToOneField(AParentModel)

            class Meta:
                register = False

        parent_obj1 = AParentModel.objects.new(name='parent1')
        AParentModel.objects.new(name='parent2')

        AChildModel.objects.new(parent=parent_obj1)

        child_obj1 = AChildModel.objects.get(parent__name='parent1')
        self.assertEqual(child_obj1.parent, parent_obj1)

    def test_set_illigal_object(self):
        from stdnet import odm
        from djangostdnet import models

        class AParentModel(models.Model):
            name = odm.CharField()

            class Meta:
                register = False

        class AChildModel(models.Model):
            parent = models.OneToOneField(AParentModel)

            class Meta:
                register = False

        parent_obj = AParentModel.objects.new()
        with self.assertRaises(ValueError):
            parent_obj.achildmodel_parent = object()

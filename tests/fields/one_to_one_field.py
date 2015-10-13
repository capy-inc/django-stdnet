from ..testcase import BaseTestCase


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

        self.finish_defining_models()
        self.create_table_for_model(ADjangoParentModel)
        self.create_table_for_model(ADjangoChildModel)

        # create stdnet relation, create django relation implicitly
        parent_obj1 = AParentModel.objects.new(name='parent1')
        child_obj1 = AChildModel.objects.new(parent=parent_obj1)
        self.assertEqual(child_obj1.parent, parent_obj1)
        self.assertEqual(child_obj1, parent_obj1.achildmodel)

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
        parent_obj1.achildmodel = child_obj1
        parent_obj1.achildmodel.save()
        parent_dj_obj1 = ADjangoParentModel.objects.get(pk=parent_obj1.pkvalue())
        child_dj_obj1 = ADjangoChildModel.objects.get(pk=child_obj1.pkvalue())
        self.assertEqual(child_dj_obj1, parent_dj_obj1.adjangochildmodel)

        # create django relation, create stdnet relation implicitly
        parent_dj_obj3 = ADjangoParentModel.objects.create(name='parent3')
        child_dj_obj3 = ADjangoChildModel.objects.create(parent=parent_dj_obj3)

        parent_obj3 = AParentModel.objects.get(id=parent_dj_obj3.pk)
        child_obj3 = AChildModel.objects.get(id=child_dj_obj3.pk)
        self.assertEqual(child_obj3.parent, parent_obj3)
        self.assertEqual(child_obj3, parent_obj3.achildmodel)

        # change parent
        parent_dj_obj4 = ADjangoParentModel.objects.create(name='parent4')
        child_dj_obj3.parent = parent_dj_obj4
        child_dj_obj3.save()

        parent_obj4 = AParentModel.objects.get(id=parent_dj_obj4.pk)
        child_obj3 = AChildModel.objects.get(id=child_dj_obj3.pk)
        self.assertEqual(child_obj3.parent, parent_obj4)
        self.assertEqual(child_obj3, parent_obj4.achildmodel)

        # change child
        parent_dj_obj3.adjangochildmodel = child_dj_obj3
        parent_dj_obj3.adjangochildmodel.save()
        parent_obj3 = AParentModel.objects.get(id=parent_dj_obj3.pk)
        child_obj3 = AChildModel.objects.get(id=child_dj_obj3.pk)
        self.assertEqual(child_obj3, parent_obj3.achildmodel)

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

    def test_related_name(self):
        from stdnet import odm
        from djangostdnet import models

        class AParentModel(models.Model):
            name = odm.CharField()

            class Meta:
                register = False

        class AChildModel(models.Model):
            parent = models.OneToOneField(AParentModel, related_name='child')

            class Meta:
                register = False

        parent_obj = AParentModel.objects.new()
        child_obj = AChildModel.objects.new(parent=parent_obj)
        self.assertEqual(parent_obj.child, child_obj)

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
            parent_obj.achildmodel = object()

    def test_model_deletion_from_stdnet_child(self):
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

        self.finish_defining_models()
        self.create_table_for_model(ADjangoParentModel)
        self.create_table_for_model(ADjangoChildModel)

        parent_obj = AParentModel.objects.new(name='parent')
        child_obj = AChildModel.objects.new(parent=parent_obj)

        child_obj.delete()
        parent_obj = AParentModel.objects.get(id=parent_obj.id)
        with self.assertRaises(AChildModel.DoesNotExist):
            parent_obj.achildmodel

        self.assertEqual(len(ADjangoParentModel.objects.all()), 1)
        self.assertEqual(len(ADjangoChildModel.objects.all()), 0)
        self.assertEqual(len(AParentModel.objects.all()), 1)
        self.assertEqual(len(AChildModel.objects.all()), 0)

    def test_model_deletion_from_stdnet_parent(self):
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

        self.finish_defining_models()
        self.create_table_for_model(ADjangoParentModel)
        self.create_table_for_model(ADjangoChildModel)

        parent_obj = AParentModel.objects.new(name='parent')
        AChildModel.objects.new(parent=parent_obj)

        # cascading deletion
        parent_obj.delete()

        self.assertEqual(len(ADjangoParentModel.objects.all()), 0)
        self.assertEqual(len(ADjangoChildModel.objects.all()), 0)
        self.assertEqual(len(AParentModel.objects.all()), 0)
        self.assertEqual(len(AChildModel.objects.all()), 0)

    def test_model_deletion_from_django_child(self):
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

        self.finish_defining_models()
        self.create_table_for_model(ADjangoParentModel)
        self.create_table_for_model(ADjangoChildModel)

        parent_dj_obj = ADjangoParentModel.objects.create(name='parent')
        child_dj_obj = ADjangoChildModel.objects.create(parent=parent_dj_obj)

        child_dj_obj.delete()
        parent_dj_obj = ADjangoParentModel.objects.get(pk=parent_dj_obj.pk)
        with self.assertRaises(ADjangoChildModel.DoesNotExist):
            parent_dj_obj.adjangochildmodel

        self.assertEqual(len(ADjangoParentModel.objects.all()), 1)
        self.assertEqual(len(ADjangoChildModel.objects.all()), 0)
        self.assertEqual(len(AParentModel.objects.all()), 1)
        self.assertEqual(len(AChildModel.objects.all()), 0)

    def test_model_deletion_from_django_parent(self):
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

        self.finish_defining_models()
        self.create_table_for_model(ADjangoParentModel)
        self.create_table_for_model(ADjangoChildModel)

        parent_dj_obj = ADjangoParentModel.objects.create(name='parent')
        ADjangoChildModel.objects.create(parent=parent_dj_obj)

        # cascading deletion
        parent_dj_obj.delete()

        self.assertEqual(len(ADjangoParentModel.objects.all()), 0)
        self.assertEqual(len(ADjangoChildModel.objects.all()), 0)
        self.assertEqual(len(AParentModel.objects.all()), 0)
        self.assertEqual(len(AChildModel.objects.all()), 0)

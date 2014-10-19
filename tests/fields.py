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

        self.create_table_for_model(ADjangoParentModel)
        self.create_table_for_model(ADjangoChildModel)

        parent_obj = AParentModel.objects.new(name='parent')
        child_obj = AChildModel.objects.new(parent=parent_obj)

        child_obj.delete()
        parent_obj = AParentModel.objects.get(id=parent_obj.id)
        with self.assertRaises(AChildModel.DoesNotExist):
            _ = parent_obj.achildmodel_parent

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

        self.create_table_for_model(ADjangoParentModel)
        self.create_table_for_model(ADjangoChildModel)

        parent_obj = AParentModel.objects.new(name='parent')
        _ = AChildModel.objects.new(parent=parent_obj)

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

        self.create_table_for_model(ADjangoParentModel)
        self.create_table_for_model(ADjangoChildModel)

        parent_dj_obj = ADjangoParentModel.objects.create(name='parent')
        child_dj_obj = ADjangoChildModel.objects.create(parent=parent_dj_obj)

        child_dj_obj.delete()
        parent_dj_obj = ADjangoParentModel.objects.get(pk=parent_dj_obj.pk)
        with self.assertRaises(ADjangoChildModel.DoesNotExist):
            _ = parent_dj_obj.adjangochildmodel

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

        self.create_table_for_model(ADjangoParentModel)
        self.create_table_for_model(ADjangoChildModel)

        parent_dj_obj = ADjangoParentModel.objects.create(name='parent')
        _ = ADjangoChildModel.objects.create(parent=parent_dj_obj)

        # cascading deletion
        parent_dj_obj.delete()

        self.assertEqual(len(ADjangoParentModel.objects.all()), 0)
        self.assertEqual(len(ADjangoChildModel.objects.all()), 0)
        self.assertEqual(len(AParentModel.objects.all()), 0)
        self.assertEqual(len(AChildModel.objects.all()), 0)


class ImageFieldTestCase(BaseTestCase):
    def test_with_django(self):
        import os
        import tempfile
        from PIL import Image
        from django.core.files import images
        from django.db import models as dj_models
        from djangostdnet import models

        class ADjangoModel(dj_models.Model):
            image = dj_models.ImageField()

        class AModel(models.Model):
            class Meta:
                django_model = ADjangoModel
                register = False

        self.create_table_for_model(ADjangoModel)

        (fd, filename) = tempfile.mkstemp()
        image = Image.new('RGB', (10, 20))
        image.save(os.fdopen(fd, 'wb'), 'gif')

        self.addCleanup(os.remove, filename)

        obj = AModel.objects.new(image=images.ImageFile(open(filename)))

        self.addCleanup(os.remove, obj.image.path)

        dj_obj = ADjangoModel.objects.get(pk=obj.id)

        dj_obj.image.open()
        self.assertEqual(dj_obj.image.read(6), 'GIF87a')

    def test_with_django_dimention_fields(self):
        import os
        import tempfile
        from PIL import Image
        from django.core.files import images
        from django.db import models as dj_models
        from djangostdnet import models

        class ADjangoModel(dj_models.Model):
            image = dj_models.ImageField(width_field='width', height_field='height')
            width = dj_models.IntegerField(null=True)
            height = dj_models.IntegerField(null=True)

        class AModel(models.Model):
            class Meta:
                django_model = ADjangoModel
                register = False

        self.create_table_for_model(ADjangoModel)

        (fd, filename) = tempfile.mkstemp()
        image = Image.new('RGB', (10, 20))
        image.save(os.fdopen(fd, 'wb'), 'gif')

        self.addCleanup(os.remove, filename)

        obj = AModel.objects.new(image=images.ImageFile(open(filename)))

        self.assertEqual(obj.width, 10)
        self.assertEqual(obj.height, 20)

        self.addCleanup(os.remove, obj.image.path)

        dj_obj = ADjangoModel.objects.get(pk=obj.id)

        dj_obj.image.open()
        self.assertEqual(dj_obj.image.read(6), 'GIF87a')
        self.assertEqual(dj_obj.width, 10)
        self.assertEqual(dj_obj.height, 20)

    def test_without_django(self):
        import os
        import tempfile
        from PIL import Image
        from django.core.files import images
        from stdnet import odm
        from djangostdnet import models

        class AModel(models.Model):
            image = models.ImageField(width_field='width', height_field='height', upload_to='image_field_test',
                                      required=False)
            width = odm.IntegerField(required=False)
            height = odm.IntegerField(required=False)

            class Meta:
                register = False

        (fd, filename) = tempfile.mkstemp()
        image = Image.new('RGB', (10, 20))
        image.save(os.fdopen(fd, 'wb'), 'gif')

        self.addCleanup(os.remove, filename)

        obj = AModel.objects.new(image=images.ImageFile(open(filename), name='test.gif'))

        self.assertEqual(obj.width, 10)
        self.assertEqual(obj.height, 20)
        self.assertEqual(obj.image.name, 'image_field_test/test.gif')

        obj = AModel.objects.get(id=obj.id)

        obj.image.open()
        self.assertEqual(obj.image.read(6), 'GIF87a')
        self.assertEqual(obj.width, 10)
        self.assertEqual(obj.height, 20)

        image_path = obj.image.path
        obj.image.delete()
        obj.delete()
        self.assertFalse(os.path.isfile(image_path))

    def test_delete_from_django(self):
        import os
        import tempfile
        from PIL import Image
        from django.core.files import images
        from django.db import models as dj_models
        from djangostdnet import models

        class ADjangoModel(dj_models.Model):
            image = dj_models.ImageField()

        class AModel(models.Model):
            class Meta:
                django_model = ADjangoModel
                register = False

        self.create_table_for_model(ADjangoModel)

        (fd, filename) = tempfile.mkstemp()
        image = Image.new('RGB', (10, 20))
        image.save(os.fdopen(fd, 'wb'), 'gif')

        self.addCleanup(os.remove, filename)

        obj = AModel.objects.new(image=images.ImageFile(open(filename)))

        dj_obj = ADjangoModel.objects.get(pk=obj.id)

        dj_obj.image.open()
        self.assertEqual(dj_obj.image.read(6), 'GIF87a')

        image_path = dj_obj.image.path
        dj_obj.image.delete()
        dj_obj.delete()
        self.assertFalse(os.path.isfile(image_path))

    def test_delete_from_django_stdnet(self):
        import os
        import tempfile
        from PIL import Image
        from django.core.files import images
        from django.db import models as dj_models
        from djangostdnet import models

        class ADjangoModel(dj_models.Model):
            image = dj_models.ImageField()

        class AModel(models.Model):
            class Meta:
                django_model = ADjangoModel
                register = False

        self.create_table_for_model(ADjangoModel)

        (fd, filename) = tempfile.mkstemp()
        image = Image.new('RGB', (10, 20))
        image.save(os.fdopen(fd, 'wb'), 'gif')

        self.addCleanup(os.remove, filename)

        obj = AModel.objects.new(image=images.ImageFile(open(filename)))

        dj_obj = ADjangoModel.objects.get(pk=obj.id)

        dj_obj.image.open()
        self.assertEqual(dj_obj.image.read(6), 'GIF87a')

        image_path = obj.image.path
        obj.image.delete()
        obj.delete()
        self.assertFalse(os.path.isfile(image_path))


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

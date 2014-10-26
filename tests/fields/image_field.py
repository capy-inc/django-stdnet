from ..testcase import BaseTestCase


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

    def test_with_django_dimension_fields(self):
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

    def test_empty_image(self):
        from django.db import models as dj_models
        from djangostdnet import models

        class ADjangoModel(dj_models.Model):
            image = dj_models.ImageField(width_field='width', height_field='height')
            width = dj_models.IntegerField(null=True)
            height = dj_models.IntegerField(null=True)

        class AModel(models.Model):

            class Meta:
                register = False
                django_model = ADjangoModel

        self.create_table_for_model(ADjangoModel)

        dj_obj = ADjangoModel.objects.create()
        obj = AModel.objects.get(id=dj_obj.pk)
        self.assertFalse(dj_obj.image)
        self.assertFalse(obj.image)
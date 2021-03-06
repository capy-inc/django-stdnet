from six import b
from ..testcase import BaseTestCase


class ImageFieldTestCase(BaseTestCase):
    def allocateImage(self):
        from django.core.files import images
        import os
        from PIL import Image
        import tempfile

        (fd, filename) = tempfile.mkstemp()
        _image = Image.new('RGB', (10, 20))
        _image.save(os.fdopen(fd, 'wb'), 'gif')
        self.addCleanup(os.remove, filename)

        return images.ImageFile(open(filename, 'rb'), name='test.gif')

    def cleanupImage(self, image):
        import os

        try:
            image_path = image.path
        except ValueError:
            image_path = None
        if image_path and os.path.isfile(image.path):
            os.remove(image.path)

    def cleanupStorage(self, storage, path):
        import shutil

        shutil.rmtree(storage.path(path))

    def test_with_django(self):
        from django.db import models as dj_models
        from djangostdnet import models

        class ADjangoModel(dj_models.Model):
            image = dj_models.ImageField()

        class AModel(models.Model):
            class Meta:
                django_model = ADjangoModel
                register = False

        self.create_table_for_model(ADjangoModel)

        image = self.allocateImage()
        obj = AModel.objects.new(image=image)
        self.addCleanup(self.cleanupImage, obj.image)

        dj_obj = ADjangoModel.objects.get(pk=obj.id)

        dj_obj.image.open()
        self.assertEqual(dj_obj.image.read(6), b('GIF87a'))

    def test_without_django(self):
        from djangostdnet import models

        class AModel(models.Model):
            image = models.ImageField(upload_to='image_field_test',
                                      required=False)

            class Meta:
                register = False

        image = self.allocateImage()
        obj = AModel.objects.new(image=image)
        self.addCleanup(self.cleanupImage, obj.image)
        self.addCleanup(self.cleanupStorage, obj.image.field.storage, 'image_field_test')

        self.assertEqual(obj.image.name, 'image_field_test/test.gif')

        obj = AModel.objects.get(id=obj.id)

        obj.image.open()
        self.assertEqual(obj.image.read(6), b('GIF87a'))

    def test_dimension_fields_with_django(self):
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

        image = self.allocateImage()
        obj = AModel.objects.new(image=image)
        self.addCleanup(self.cleanupImage, obj.image)

        self.assertEqual(obj.width, 10)
        self.assertEqual(obj.height, 20)

        dj_obj = ADjangoModel.objects.get(pk=obj.id)

        self.assertEqual(dj_obj.width, 10)
        self.assertEqual(dj_obj.height, 20)

    def test_dimension_fields_without_django(self):
        from stdnet import odm
        from djangostdnet import models

        class AModel(models.Model):
            image = models.ImageField(width_field='width', height_field='height',
                                      required=False)
            width = odm.IntegerField(required=False)
            height = odm.IntegerField(required=False)

            class Meta:
                register = False

        image = self.allocateImage()
        obj = AModel.objects.new(image=image)
        self.addCleanup(self.cleanupImage, obj.image)

        self.assertEqual(obj.width, 10)
        self.assertEqual(obj.height, 20)

        obj = AModel.objects.get(id=obj.id)

        self.assertEqual(obj.width, 10)
        self.assertEqual(obj.height, 20)

    def test_delete_from_django(self):
        import os
        from django.db import models as dj_models
        from djangostdnet import models

        class ADjangoModel(dj_models.Model):
            image = dj_models.ImageField()

        class AModel(models.Model):
            class Meta:
                django_model = ADjangoModel
                register = False

        self.create_table_for_model(ADjangoModel)

        image = self.allocateImage()
        obj = AModel.objects.new(image=image)
        self.addCleanup(self.cleanupImage, obj.image)

        dj_obj = ADjangoModel.objects.get(pk=obj.id)

        dj_obj.image.open()
        self.assertEqual(dj_obj.image.read(6), b('GIF87a'))

        image_path = dj_obj.image.path
        dj_obj.image.delete()
        dj_obj.delete()
        self.assertFalse(os.path.isfile(image_path))

    def test_delete_from_django_stdnet(self):
        import os
        from django.db import models as dj_models
        from djangostdnet import models

        class ADjangoModel(dj_models.Model):
            image = dj_models.ImageField()

        class AModel(models.Model):
            class Meta:
                django_model = ADjangoModel
                register = False

        self.create_table_for_model(ADjangoModel)

        image = self.allocateImage()
        obj = AModel.objects.new(image=image)
        self.addCleanup(self.cleanupImage, obj.image)

        dj_obj = ADjangoModel.objects.get(pk=obj.id)

        dj_obj.image.open()
        self.assertEqual(dj_obj.image.read(6), b('GIF87a'))

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

    def test_func_upload_to_with_django(self):
        import os
        from django.conf import settings
        from django.db import models as dj_models
        from djangostdnet import models

        def gen_custom_path(instance, filename):
            return os.path.join('custom_path', filename)

        class ADjangoModel(dj_models.Model):
            image = dj_models.ImageField(upload_to=gen_custom_path)

        class AModel(models.Model):
            class Meta:
                django_model = ADjangoModel
                register = False

        self.create_table_for_model(ADjangoModel)

        image = self.allocateImage()
        obj = AModel.objects.new(image=image)
        self.addCleanup(self.cleanupImage, obj.image)

        dj_obj = ADjangoModel.objects.get(pk=obj.id)

        custom_path_prefix = os.path.join(settings.MEDIA_ROOT, 'custom_path')
        self.assertTrue(obj.image.path.startswith(custom_path_prefix))
        self.assertTrue(dj_obj.image.path.startswith(custom_path_prefix))
        self.assertEqual(obj.image.path, dj_obj.image.path)

    def test_func_upload_to_without_django(self):
        import os
        from django.conf import settings
        from djangostdnet import models

        def gen_custom_path(instance, filename):
            return os.path.join('custom_path', filename)

        class AModel(models.Model):
            image = models.ImageField(upload_to=gen_custom_path)

            class Meta:
                register = False

        image = self.allocateImage()
        obj = AModel.objects.new(image=image)
        self.addCleanup(self.cleanupImage, obj.image)

        custom_path_prefix = os.path.join(settings.MEDIA_ROOT, 'custom_path')
        self.assertTrue(obj.image.path.startswith(custom_path_prefix))

    def test_strftime_upload_to_with_django(self):
        import os
        from freezegun import freeze_time
        from django.conf import settings
        from django.db import models as dj_models
        from djangostdnet import models

        class ADjangoModel(dj_models.Model):
            image = dj_models.ImageField(upload_to='custom_path/%Y%m%d')

        class AModel(models.Model):
            class Meta:
                django_model = ADjangoModel
                register = False

        self.create_table_for_model(ADjangoModel)

        image = self.allocateImage()
        with freeze_time('1990-01-01'):
            obj = AModel.objects.new(image=image)
        self.addCleanup(self.cleanupImage, obj.image)

        dj_obj = ADjangoModel.objects.get(pk=obj.id)

        custom_path_prefix = os.path.join(settings.MEDIA_ROOT, 'custom_path', '19900101')
        self.assertTrue(obj.image.path.startswith(custom_path_prefix))
        self.assertTrue(dj_obj.image.path.startswith(custom_path_prefix))
        self.assertEqual(obj.image.path, dj_obj.image.path)

    def test_strftime_upload_to_without_django(self):
        import os
        from freezegun import freeze_time
        from django.conf import settings
        from djangostdnet import models

        class AModel(models.Model):
            image = models.ImageField(upload_to='custom_path/%Y%m%d')

            class Meta:
                register = False

        image = self.allocateImage()
        with freeze_time('1990-01-01'):
            obj = AModel.objects.new(image=image)
        self.addCleanup(self.cleanupImage, obj.image)

        custom_path_prefix = os.path.join(settings.MEDIA_ROOT, 'custom_path', '19900101')
        self.assertTrue(obj.image.path.startswith(custom_path_prefix))

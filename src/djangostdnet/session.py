from datetime import datetime
from django.conf import settings
from django.utils import timezone
from stdnet import odm
from stdnet.odm import session
from . import fields as fields_mod


UNDEFINED = object()


class Session(session.Session):
    def add(self, instance, modified=True, **params):
        from .models import Model

        if (modified
            and isinstance(instance, Model)
            and hasattr(instance, '_django_meta')
            and hasattr(instance._django_meta, 'model')):
            self._ensure_django_instance(instance)
        return super(Session, self).add(instance, modified, **params)

    def _ensure_django_instance(self, instance):
        django_model = instance._django_meta.model
        modified = False
        if instance._instance is None:
            try:
                instance._instance = django_model.objects.get(pk=instance.pkvalue())
            except django_model.DoesNotExist:
                modified = True
                instance._instance = django_model()
                instance._instance.pk = instance.pkvalue()
        if instance._instance.pk is None:
            creation = True
            modified = True
            # primary key will be obtained from django model instance
            fields = [field for field in instance._meta.fields
                      if field != instance._meta.pk]
        else:
            creation = False
            fields = instance._meta.fields

        for field in fields:
            if isinstance(field, (odm.ForeignKey, fields_mod.OneToOneField)):
                field_name = '%s_id' % field.name
                field_value = field.get_value(instance).pkvalue()
            else:
                field_name = field.name
                field_value = field.get_value(instance)
            if getattr(instance._instance, field_name, UNDEFINED) != field_value:
                modified = True
                setattr(instance._instance, field_name, field_value)

        if modified:
            instance._instance.save()

        # assign django model's pk to stdnet model
        if creation:
            instance._meta.pk.set_value(instance, instance._instance.pk)

    def add_from_django_object(self, manager, django_obj):
        model = manager.model
        pk = model._meta.pk
        modified = False
        try:
            instance = manager.get(**{pk.name: django_obj.pk})
            creation = False
        except manager.model.DoesNotExist:
            instance = manager()
            creation = True
            modified = True

        fields = [field for field in model._meta.fields
                  if field != pk]

        instance._instance = django_obj

        for field in fields:
            if isinstance(field, (odm.ForeignKey, fields_mod.OneToOneField)):
                field_name = '%s_id' % field.name
            else:
                field_name = field.name

            django_field_value = getattr(django_obj, field_name)
            field_value = getattr(instance, field_name, UNDEFINED)

            if isinstance(field, odm.DateTimeField):
                # adjust timezone
                field_value = getattr(instance, field_name, UNDEFINED)

                if isinstance(field_value, datetime) and settings.USE_TZ:
                    default_timezone = timezone.get_default_timezone()
                    field_value = timezone.make_aware(field_value, default_timezone)

            if field_value != django_field_value:
                modified = True
                setattr(instance, field_name, django_field_value)

        if creation:
            pk.set_value(instance, django_obj.pk)

        if modified:
            # shortcut the add implementation
            super(Session, self).add(instance)

    def delete_from_django_object(self, manager, django_obj):
        model = manager.model
        pk = model._meta.pk
        try:
            instance = manager.get(**{pk.name: django_obj.pk})
            self.delete(instance)
        except model.DoesNotExist:
            pass

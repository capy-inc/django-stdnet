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

        if modified:
            self._check_auto_now_and_auto_now_add(instance)

        created = False
        if (modified
            and isinstance(instance, Model)
            and hasattr(instance, '_django_meta')
            and hasattr(instance._django_meta, 'model')):
            created = self._ensure_django_instance(instance)
        if created:
            return self.query(self.model(instance)).get(id=instance.id)
        else:
            return super(Session, self).add(instance, modified, **params)

    def _check_auto_now_and_auto_now_add(self, instance):
        now = datetime.now()
        for field in instance._meta.fields:
            if isinstance(field, fields_mod.DateTimeField):
                if field.get_value(instance) is None and field.auto_now_add:
                    field.set_value(instance, now)
                if field.auto_now:
                    field.set_value(instance, now)

    def _ensure_django_instance(self, instance):
        django_model = instance._django_meta.model
        modified = False
        try:
            django_instance = django_model.objects.get(pk=instance.pkvalue())
        except django_model.DoesNotExist:
            modified = True
            django_instance = django_model()
            django_instance.pk = instance.pkvalue()
        if django_instance.pk is None:
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
            if getattr(django_instance, field_name, UNDEFINED) != field_value:
                modified = True
                setattr(django_instance, field_name, field_value)

        if modified:
            # when creation, the instance will be created implicitly by add_from_django_object
            # via post_commit signal of the django instance
            django_instance.save()

        # assign django model's pk to stdnet model
        if creation:
            instance._meta.pk.set_value(instance, django_instance.pk)

        return creation

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

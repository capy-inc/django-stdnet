# -*- encoding: utf8 -*-
import logging
from inspect import isclass

from django.conf import settings
from django.db import models
from django.db.models import signals
from six import with_metaclass
from stdnet import odm
from .mapper import Mapper
from .fields import OneToOneField


logger = logging.getLogger(__name__)


mapper = Mapper(install_global=True)


_mapping = {
    models.AutoField: odm.AutoIdField,
    models.CharField: lambda field: odm.SymbolField if field.db_index or field.primary_key else odm.CharField,
    models.IntegerField: odm.IntegerField,
    models.FloatField: odm.FloatField,
    models.BooleanField: odm.BooleanField,
    models.DateField: odm.DateField,
    models.DateTimeField: odm.DateTimeField,
    models.ForeignKey: odm.ForeignKey,
    models.OneToOneField: OneToOneField,
}


def register_field_mapping(django_field, stdnet_field_or_callable):
    _mapping[django_field] = stdnet_field_or_callable


class ModelMeta(odm.ModelType):
    @staticmethod
    def proxy__getattr__(instance, name):
        django_meta = getattr(instance, '_django_meta', None)
        attr = getattr(django_meta.model, name, None)
        if attr is not None:
            django_model_attr = getattr(models.Model, name, None)
            if attr == django_model_attr:
                raise AttributeError("Unsupported attribute of Django Model: %s", name)
            if isinstance(attr, property):
                return attr.__get__(instance, instance.__class__)
            elif callable(attr):
                return attr.__func__.__get__(instance, instance.__class__)
            # else:
            #     return attr
        raise AttributeError(name)

    def __new__(mcs, name, bases, dct):
        meta = dct.get('Meta', None)
        meta_model = getattr(meta, 'django_model', None)
        if meta_model:
            class Meta(object):
                model = meta_model

            del meta.django_model
            dct['_django_meta'] = Meta

            # proxy for original methods
            dct['__getattr__'] = mcs.proxy__getattr__
            dct['_instance'] = None
            # generate odm fields by django orm fields
            for field in meta_model._meta.fields:
                # when overriden on StdnetModel
                if field.name in dct:
                    continue

                field_params = {
                    'required': not (field.blank or field.null),
                    'index': field.db_index,
                    'unique': field.unique,
                    'primary_key': field.primary_key
                }
                if field.__class__ in _mapping:
                    odm_field_or_callable = _mapping[field.__class__]
                    if isclass(odm_field_or_callable) and issubclass(odm_field_or_callable, (odm.ForeignKey, OneToOneField)):
                        odm_field = odm_field_or_callable
                        rels = [meta for meta in mapper.registered_models
                                if hasattr(meta.model, '_django_meta') and meta.model._django_meta.model == field.rel.to]
                        if len(rels) != 1:
                            raise ValueError("Can't make implicit model relation: %s", field.name)
                        model = rels[0].model
                        dct[field.name] = odm_field(model, **field_params)
                    else:
                        if isclass(odm_field_or_callable) and issubclass(odm_field_or_callable, odm.Field):
                            odm_field = odm_field_or_callable
                        else:
                            callable_obj = odm_field_or_callable
                            odm_field = callable_obj(field)
                        dct[field.name] = odm_field(**field_params)
                else:
                    logger.warn("not supported for field type: %s", field.__class__.__name__)

        meta_backend = getattr(meta, 'backend', 'default')
        if hasattr(meta, 'backend'):
            del meta.backend
        meta_read_backend = getattr(meta, 'read_backend', None)
        if hasattr(meta, 'read_backend'):
            del meta.read_backend

        if meta_backend in settings.STDNET_BACKENDS:
            value = settings.STDNET_BACKENDS[meta_backend]
            if isinstance(value, dict):
                meta_backend = value['BACKEND']
            else:
                meta_backend = value

        if meta_read_backend in settings.STDNET_BACKENDS:
            value = settings.STDNET_BACKENDS[meta_read_backend]
            if isinstance(value, dict):
                meta_read_backend = value['READ_BACKEND']
            else:
                meta_read_backend = value

        model = odm.ModelType.__new__(mcs, name, bases, dct)
        mapper.register(model, meta_backend, meta_read_backend)

        if meta_model:
            def post_save_handle(instance, **kwargs):
                manager = mapper[model]
                manager.session().add_from_django_object(manager, instance)

            def post_delete_handle(instance, **kwargs):
                manager = mapper[model]
                manager.session().delete_from_django_object(manager, instance)

            signals.post_save.connect(post_save_handle, sender=meta_model, weak=False)
            signals.post_delete.connect(post_delete_handle, sender=meta_model, weak=False)

        return model


class DjangoStdnetModel(with_metaclass(ModelMeta, odm.StdModel)):
    pass


Model = DjangoStdnetModel

__all__ = ('Model', 'OneToOneField')
# -*- encoding: utf8 -*-
from collections import defaultdict
from distutils.version import LooseVersion
import logging
from inspect import isclass
import threading

from django.conf import settings
from django.db import models
from django.db.models import signals
from six import with_metaclass
from stdnet import odm
from . import DJANGO_VERSION
from .mapper import Mapper
from .fields import OneToOneField, ImageField, IPAddressField, DecimalField, DateTimeField


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
    models.ManyToManyField: odm.ManyToManyField,
    models.OneToOneField: OneToOneField,
    models.ImageField: ImageField,
    models.IPAddressField: IPAddressField
}


def register_field_mapping(django_field, stdnet_field_or_callable):
    _mapping[django_field] = stdnet_field_or_callable


class Registry(object):
    def __init__(self):
        self.django_to_stdnet = {}
        self.stdnet_to_django = {}

    def register(self, django_model, stdnet_model):
        self.django_to_stdnet[django_model] = stdnet_model
        self.stdnet_to_django[stdnet_model] = django_model

    def get_django_model(self, stdnet_model):
        return self.stdnet_to_django[stdnet_model]

    def get_stdnet_model(self, django_model):
        return self.django_to_stdnet[django_model]


registry = Registry()


class ThreadGate(object):
    def __init__(self):
        self.states = defaultdict(int)

    def __enter__(self):
        thread_id = threading.current_thread().ident
        already_in_gate = thread_id in self.states
        self.states[thread_id] += 1
        return already_in_gate

    def __exit__(self, exc_type, exc_val, exc_tb):
        thread_id = threading.current_thread().ident
        self.states[thread_id] -= 1
        if self.states[thread_id] == 0:
            del self.states[thread_id]


if LooseVersion('1.8') <= DJANGO_VERSION:
    def get_fields(opts):
        return opts.get_fields()
else:
    # prior to 1.8
    def get_fields(opts):
        return opts.fields + opts.many_to_many


class ModelMeta(odm.ModelType):
    @staticmethod
    def proxy__getattr__(instance, name):
        django_meta = getattr(instance, '_django_meta', None)
        # retrieve from instance dict first for descriptor which may raise AttributeError
        attr = (django_meta.model.__dict__.get(name)
                or getattr(django_meta.model, name, None))
        if attr is not None:
            django_model_attr = (models.Model.__dict__.get(name)
                                 or getattr(models.Model, name, None))
            if attr == django_model_attr:
                raise AttributeError("Unsupported attribute of Django Model: %s", name)
            if isinstance(attr, property):
                return attr.__get__(instance, instance.__class__)
            elif callable(getattr(attr, '__func__', None)):
                return attr.__func__.__get__(instance, instance.__class__)
            elif callable(getattr(attr, '__get__', None)):
                return attr.__get__(instance, instance.__class__)
            # else:
            #     return attr
        raise AttributeError(name)

    def __new__(mcs, name, bases, dct):
        meta = dct.get('Meta', None)
        meta_model = getattr(meta, 'django_model', None)
        meta_through = {}
        if meta_model:
            class Meta(object):
                model = meta_model

            del meta.django_model
            dct['_django_meta'] = Meta

            # proxy for original methods
            dct['__getattr__'] = mcs.proxy__getattr__
            dct['_instance'] = None
            # generate odm fields by django orm fields
            for field in get_fields(meta_model._meta):
                # when overriden on StdnetModel
                if field.name in dct:
                    continue

                if not getattr(field, 'concrete', True):
                    continue

                field_params = {
                    'required': not (field.blank or field.null),
                    'index': field.db_index,
                    'unique': field.unique,
                    'primary_key': field.primary_key
                }
                if field.__class__ in _mapping:
                    odm_field_or_callable = _mapping[field.__class__]
                    if isclass(odm_field_or_callable) and issubclass(odm_field_or_callable, (odm.ForeignKey,
                                                                                             OneToOneField,
                                                                                             odm.ManyToManyField)):
                        odm_field = odm_field_or_callable
                        rels = [meta for meta in mapper.registered_models
                                if hasattr(meta.model, '_django_meta') and meta.model._django_meta.model == field.rel.to]
                        if len(rels) != 1:
                            raise ValueError("Can't make implicit model relation: %s", field.name)
                        model = rels[0].model
                        if field.__class__ == models.ManyToManyField:
                            field_params['related_name'] = field.rel.related_name
                        dct[field.name] = odm_field(model, **field_params)
                        if field.__class__ == models.ManyToManyField:
                            meta_through[field.name] = field.rel.through
                    elif isclass(odm_field_or_callable) and issubclass(odm_field_or_callable, ImageField):
                        odm_field = odm_field_or_callable
                        dct[field.name] = odm_field(upload_to=field.upload_to, **field_params)
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
        if meta_read_backend is None:
            meta_read_backend = meta_backend

        if meta_backend in settings.STDNET_BACKENDS:
            value = settings.STDNET_BACKENDS[meta_backend]
            if isinstance(value, dict):
                meta_backend = value['BACKEND']
            else:
                meta_backend = value

        if meta_read_backend in settings.STDNET_BACKENDS:
            value = settings.STDNET_BACKENDS[meta_read_backend]
            if isinstance(value, dict):
                # first obtain READ_BACKEND, fallback to BACKEND which must be.
                meta_read_backend = value.get('READ_BACKEND', value['BACKEND'])
            else:
                meta_read_backend = value

        model = odm.ModelType.__new__(mcs, name, bases, dct)
        model._meta.object_name = name
        mapper.register(model, meta_backend, meta_read_backend)

        if meta_model:
            registry.register(meta_model, model)

            # TODO move pre_save handler from stdnet defined in session here.
            def post_save_handle_from_django(instance, **kwargs):
                manager = mapper[model]
                manager.session().add_from_django_object(manager, instance)

            def post_delete_handle_from_django(instance, **kwargs):
                manager = mapper[model]
                manager.session().delete_from_django_object(manager, instance)

            def post_delete_handle_from_stdnet(_ev, _model, instances=[], **kwargs):
                meta_model.objects.filter(pk__in=instances).delete()

            signals.post_save.connect(post_save_handle_from_django, sender=meta_model, weak=False)
            # XXX Why not this is pre_delete?
            signals.post_delete.connect(post_delete_handle_from_django, sender=meta_model, weak=False)
            mapper.post_delete.bind(post_delete_handle_from_stdnet, sender=model)

        # for many-to-many
        if meta_through:
            for field_name in meta_through:

                m2m_gate = ThreadGate()

                # To obtain relation manager in stdnet, pass field_name through closure
                def f(m2m_gate, meta_through, field_name):
                    meta_rel_model = meta_through[field_name]

                    def m2m_changed_handle_from_django(instance, action, model, pk_set, **kwargs):
                        with m2m_gate as already_in_gate:
                            if already_in_gate:
                                return

                            source_instance = registry.get_stdnet_model(instance.__class__).objects.get(id=instance.pk)
                            collection = getattr(source_instance, field_name)
                            target_model = registry.get_stdnet_model(model)
                            # Need measurement. get/set per each vs. bulk processing for KVS
                            if action == 'post_add':
                                for pk in pk_set:
                                    collection.add(target_model.objects.get(id=pk))
                            elif action == 'pre_remove':
                                for pk in pk_set:
                                    collection.remove(target_model.objects.get(id=pk))

                    # XXX multiple many-to-many relation with same models???
                    # XXX Is weak=False needed actually??
                    signals.m2m_changed.connect(m2m_changed_handle_from_django, sender=meta_rel_model, weak=False)

                f(m2m_gate, meta_through, field_name)

                def f2(m2m_gate, field_name):
                    through_model = model._meta.related[field_name].model

                    def post_commit_handle_from_stdnet(_ev, model, instances=(), **kwargs):
                        with m2m_gate as already_in:
                            if already_in:
                                return

                            source_field, target_field = model._meta.fields[-3:-1]
                            for instance in instances:
                                source_value = source_field.get_value(instance)
                                target_value = target_field.get_value(instance)
                                source_instance = registry.get_django_model(source_value.__class__).objects.get(id=source_value.id)
                                collection = getattr(source_instance, field_name)
                                target_instance = registry.get_django_model(target_value.__class__).objects.get(id=target_value.id)
                                collection.add(target_instance)

                    def pre_delete_handle_from_stdnet(_ev, model, instances=(), **kwargs):
                        with m2m_gate as already_in_gate:
                            if already_in_gate:
                                return

                            source_field, target_field = model._meta.fields[-3:-1]
                            for instance in instances:
                                source_value = source_field.get_value(instance)
                                target_value = target_field.get_value(instance)
                                source_instance = registry.get_django_model(source_value.__class__).objects.get(id=source_value.id)
                                collection = getattr(source_instance, field_name)
                                target_instance = registry.get_django_model(target_value.__class__).objects.get(id=target_value.id)
                                collection.remove(target_instance)

                    mapper.post_commit.bind(post_commit_handle_from_stdnet, sender=through_model)
                    mapper.pre_delete.bind(pre_delete_handle_from_stdnet, sender=through_model)

                f2(m2m_gate, field_name)

        return model


class DjangoStdnetModel(with_metaclass(ModelMeta, odm.StdModel)):
    class Meta:
        abstract = True


Model = DjangoStdnetModel

__all__ = ('Model', 'OneToOneField', 'ImageField', 'IPAddressField', 'DecimalField', 'DateTimeField')
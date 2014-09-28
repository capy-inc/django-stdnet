from decimal import Decimal
from django.db.models.fields import files
from stdnet import odm
from stdnet.odm import related
from stdnet.odm.globals import JSPLITTER


class LazyOneToOneField(related.LazyProxy):
    def load(self, instance, session=None, backend=None):
        if session is None:
            session = instance._meta.model.session()
        qs = session.query(self.field.model)
        return qs.get(**{self.field.name: instance})

    def __set__(self, instance, value):
        field = self.field
        if instance is None:
            raise AttributeError("%s must be accessed via instance" %
                                 field.related_name)
        if value is not None and not isinstance(value, field.model):
            raise ValueError(
                'Cannot assign "%r": "%s" must be a "%s" instance.' %
                (value, field.related_name, field.model._meta.name))

        cache_name = self.field.get_cache_name()
        setattr(value, self.field.attname, instance.pkvalue())
        setattr(value, cache_name, instance)


class OneToOneField(odm.Field):
    '''A field defining a :ref:`one-to-one <one-to-one>` objects
    relationship.
Requires a positional argument: the class to which the model is related.
For example::

    class PublicKey(odm.StdModel):
        data = odm.CharField()

    class PrivateKey(odm.StdModel):
        public_key = odm.OneToOneField(PublicKey, related_name='private_key')
        data = odm.CharField()

To create a recursive relationship, an object that has a one-to-one
relationship with itself use::

    odm.OneToOneKey('self')

Behind the scenes, stdnet appends "_id" to the field name to create
its field name in the back-end data-server. In the above example,
the database field for the ``PrivateKey`` model will have a ``public_key_id`` field.

.. attribute:: related_name

    Optional name to use for the relation from the related object
    back to ``self``.
'''
    type = 'related object'
    internal_type = 'numeric'
    python_type = int
    proxy_class = odm.LazyForeignKey
    proxy_class_reverse = LazyOneToOneField

    def __init__(self, model, related_name=None, **kwargs):
        super(OneToOneField, self).__init__(**kwargs)
        if not model:
            raise odm.FieldError('Model not specified')
        self.relmodel = model
        self.related_name = related_name

    def register_with_related_model(self):
        # add the RelatedManager proxy to the model holding the field
        setattr(self.model, self.name, self.proxy_class(self))
        related.load_relmodel(self, self._set_relmodel)

    def _set_relmodel(self, relmodel):
        self.relmodel = relmodel
        meta = self.relmodel._meta
        if not self.related_name:
            self.related_name = '_'.join([self.model._meta.name, self.name])
        if (self.related_name not in meta.related and
            self.related_name not in meta.dfields):
            self._register_with_related_model()
        else:
            raise odm.FieldError('Duplicated related name "{0} in model "{1}" '
                                 'and field {2}'.format(self.related_name,
                                                        meta, self))

    def _register_with_related_model(self):
        proxy = self.proxy_class_reverse(self)
        setattr(self.relmodel, self.related_name, proxy)
        self.relmodel._meta.related[self.related_name] = proxy
        self.relmodel_proxy = proxy

    def get_attname(self):
        return '%s_id' % self.name

    def get_value(self, instance, *bits):
        related = getattr(instance, self.name)
        return related.get_attr_value(bits) if bits else related

    def set_value(self, instance, value):
        if isinstance(value, self.relmodel):
            setattr(instance, self.name, value)
            return value
        else:
            return super(OneToOneField, self).set_value(instance, value)

    def register_with_model(self, name, model):
        super(OneToOneField, self).register_with_model(name, model)
        if not model._meta.abstract:
            self.register_with_related_model()

    def scorefun(self, value):
        if isinstance(value, self.relmodel):
            return value.scorefun()
        else:
            raise odm.FieldValueError('cannot evaluate score of {0}'.format(value))

    def to_python(self, value, backend=None):
        if isinstance(value, self.relmodel):
            return value.pkvalue()
        elif value:
            return self.relmodel._meta.pk.to_python(value, backend)
        else:
            return value
    json_serialise = to_python

    def filter(self, session, name, value):
        fname = name.split(JSPLITTER)[0]
        if fname in self.relmodel._meta.dfields:
            return session.query(self.relmodel, fargs={name: value})

    def get_sorting(self, name, errorClass):
        return self.relmodel._meta.get_sorting(name, errorClass)

    def get_lookup(self, name, errorClass=ValueError):
        if name:
            bits = name.split(JSPLITTER)
            fname = bits.pop(0)
            field = self.relmodel._meta.dfields.get(fname)
            meta = self.relmodel._meta
            if field:   # it is a field
                nested = [(self.attname, meta)]
                remaining = JSPLITTER.join(bits)
                name, _nested = field.get_lookup(remaining, errorClass)
                if _nested:
                    nested.extend(_nested)
                return (name, nested)
            else:
                raise errorClass('%s not a valid field for %s' % (fname, meta))
        else:
            return super(OneToOneField, self).get_lookup(name, errorClass)


class ImageField(odm.Field):
    def __init__(self, width_field=None, height_field=None, *args, **kwargs):
        super(ImageField, self).__init__(*args, **kwargs)
        self._width_field = width_field
        self._height_field = height_field

    def register_with_model(self, name, model):
        super(ImageField, self).register_with_model(name, model)
        setattr(model, name, files.ImageFileDescriptor(self))

    def update_dimension_fields(self, *args, **kwargs):
        delegate_func = files.ImageField.update_dimension_fields.__func__.__get__(self, self.__class__)
        return delegate_func(*args, **kwargs)

    def _get_original_model_field(self):
        django_meta = getattr(self.model, '_django_meta', None)
        if django_meta is not None:
            return django_meta.model._meta.get_field_by_name(self.name)[0]

    @property
    def width_field(self):
        if self._width_field is not None:
            return self._width_field

        field = self._get_original_model_field()
        if field:
            return field.width_field

    @width_field.setter
    def width_field(self, value):
        self._width_field

    @property
    def height_field(self):
        if self._height_field is not None:
            return self._height_field

        field = self._get_original_model_field()
        if field:
            return field.height_field

    @height_field.setter
    def height_field(self, value):
        self._height_field


class IPAddressField(odm.SymbolField):
    pass


class DecimalField(odm.IntegerField):
    type = 'decimal'
    internal_type = 'numeric'
    python_type = Decimal


__all__ = ['OneToOneField', 'ImageField', 'IPAddressField', 'DecimalField']
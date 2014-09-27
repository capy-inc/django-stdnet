from time import time
from stdnet.odm import session
from stdnet import odm


class TTLBackendQueryClassWrapper(object):
    def __init__(self, query_class):
        self.query_class = query_class

    def __call__(self, obj, **kwargs):
        return TTLBackendQueryWrapper(self.query_class, obj, **kwargs)


class TTLBackendQueryWrapper(object):
    def __init__(self, query_class, obj, **kwargs):
        self.query = query_class(obj, **kwargs)

    def __getattr__(self, item):
        return getattr(self.query, item)

    def _wrap_purge_expired(self, callback):
        def f(result):
            return callback(self._purge_expired(result))
        return f

    def _purge_expired(self, items):
        result = []
        for item in items:
            ttl_fields = [field for field in item._meta.fields
                          if isinstance(field, TTLField)]
            if len(ttl_fields) != 1:
                raise IOError("Support only one ttl field per model: %s", item._meta.model)
            ttl_field = ttl_fields[0]
            ttl_value = ttl_field.get_value(item)
            if ttl_value is not None and ttl_value < 0:
                item.delete()
            else:
                result.append(item)
        return result

    def items(self, slic=None, callback=None):
        if callback is not None:
            callback = self._wrap_purge_expired(callback)
            return getattr(self.query, 'items')(slic, callback)
        else:
            items = getattr(self.query, 'items')(slic, None)
            return self._purge_expired(items)


class TTLBackendMiddleware(object):
    def __init__(self, backend):
        self.backend = backend
        self.Query = TTLBackendQueryClassWrapper(backend.Query)

    def __getattr__(self, name):
        return getattr(self.backend, name)


class TTLManager(session.Manager):
    @property
    def read_backend(self):
        original_backend = super(TTLManager, self).read_backend
        return TTLBackendMiddleware(original_backend)

    @property
    def backend(self):
        original_backend = super(TTLManager, self).backend
        return TTLBackendMiddleware(original_backend)


class TTLField(odm.CharField):
    def set_get_value(self, instance, value):
        if value is not None:
            now = time()
            return ':'.join([str(int(now)), str(int(value))])

    def to_python(self, value, backend=None):
        if isinstance(value, int):
            return value
        elif isinstance(value, basestring):
            now = time()
            t, delta = [int(v) for v in value.split(':')]
            return t + delta - int(now)
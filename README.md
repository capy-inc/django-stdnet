# django-stdnet


## Basic Components


### Stdnet

- Object data mapper and advanced query manager for redis
- Provides Django similar APIs for modeling and querying
- http://lsbardel.github.io/python-stdnet/

``` python
class Author(odm.StdModel):
    name = odm.SymbolField()
    email = odm.CharField()


author = mapper.author.get(name='foo')
author.name = 'bar'
author.save()
```

That's stored in Redis

```
main.author:obj:1
main.author:id
main.author:ids
main.author:idx:name:foo
...
```


### django-stdnet

- Product using Stdnet
- Generate Stdnet model from Django model definition on runtime, as work as ModelForm, ModelAdmin
- Addition, provides utility APIs, method delegation and data synchronization at saving

``` python
class Author(models.Model):
    name = models.CharField(db_index=True)
    email = models.CharField()


class AuthorStd(std_models.Model):
    class Meta:
        django_model = Author
```


## Basic

Define model for Django and set it in correspond Meta class.

```python
class Author(models.Model):
    name = models.CharField(db_index=True)
    email = models.CharField()


class AuthorStd(std_models.Model):
    class Meta:
        django_model = Author
```

Query works as same as Stdnet query, NOT Django query.

```python
author = AuthorStd.objects.get(name='foo')
```


## Override Definition

Generated fields can be overriden by defined manually.
Also can expand the definition.

```python
class Author(models.Model):
    name = models.CharField(db_index=True)
    email = models.CharField()


class AuthorStd(std_models.Model):
    email = odm.SymbolField()           # email would also be indexable
    arrival_count = odm.IntegerField()  # Stdnet model has original value
                                        # which Django model haven’t

    class Meta:
        django_model = Author
```


## Data Synchronization

Django model related django-stdnet model is bi-direct synchronized automatically at post saving by signal.
Its easier to import Django model objects into django-stdnet model, fetch them then just save it.


## Model Relation

Django and Stdnet provide their original ForeignKey feature similar.
django-stdnet model is-a Stdnet model and introduces relation from Django model definition.

```python
class Author(models.Model):
    name = models.CharField()

class Book(models.Model):
    author = models.ForeignKey(Author)

class AuthorStd(std_models.Model):
    class Meta:
        django_model = Author

class BookStd(std_models.Model):
    class Meta:
        django_model = Book


# implies

class BookStd(std_models.Model):
    author = odm.ForeignKey(AuthorStd)
    class Meta:
        django_model = Book
```

## Connection Setting

Connecting to destination is customizable in variaous ways.

- STDNET_BACKENDS in Django settings
  - default can be replaced
    - a connection string
    - dict(BACKEND='...', READ_BACKEND='...') of the string
  - can be defined named backend settings used in django-stdnet model Meta class
- django-stdnet model Meta class can be set only backend or both backend and read_backend which are connection string or name of named backend setting


## Time To Live

Stdnet doesn’t support it now.
django-stdnet model supports it by their custom Manager/Field.
Only one ttl field support in a model.
Set a ttl in second.

```python
from djangostdnet import ttl as ttl_mod


class Challenge(std_models.Model):
    ttl = ttl_mod.TTLField()

    manager_class = ttl_mod.TTLManager
```


## Method Delegation
django-stdnet model borrow correspond Django model method for delegation.
It could be method Mix-in, but definitly, model’s method is not mix-in method.

```python
class Author(models.Model):
    name = models.CharField()

    def hello(self, name):
        return 'hello %s, I am %s' % (name, self.name)


class AuthorStd(std_models.Model):
    class Meta:
        django_model = Author


author = AuthorStd.objects.new(name='author')
author.hello('guest')
# => 'hello guest, I am author'
```


## Various Fields

Some additional fields for Django.

- ImageField
- OneToOneField
- DateTimeField to support auto_now/auto_now_add


## Caveat


### Index Strategy

Indexed field is only queryable.

- In Django model (RDB), not indexed field is also queryable, only affect for speed
- In Stdnet model (Redis), not indexed field is not queryable

Override field definition to make index if need.

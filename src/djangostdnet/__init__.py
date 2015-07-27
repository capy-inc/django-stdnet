from distutils.version import LooseVersion
import django

DJANGO_VERSION = LooseVersion(django.get_version())

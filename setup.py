from setuptools import setup, find_packages


setup(
    name='django-stdnet',
    version='0.0.1',
    description='a bridge between django and stdnet',
    author='MURAOKA Yusuke',
    author_email='yusuke@jbking.org',
    url='',
    packages=find_packages('src'),
    package_dir={
        '': 'src',
    },
    install_requires=['python-stdnet'],
)

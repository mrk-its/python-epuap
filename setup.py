import os
from setuptools import setup

README = open(os.path.join(os.path.dirname(__file__), 'README')).read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='epuap',
    version='0.1',
    packages=['epuap'],
    install_requires=[
        'lxml==3.4.1',
        'requests==2.4.3',
    ],
    include_package_data=True,
    long_description=README,
    url='https://github.com/mrk-its/python-epuap',
    author='mrk',
    author_email='mrk@sed.pl',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
)

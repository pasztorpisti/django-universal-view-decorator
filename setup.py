# -*- coding: utf-8 -*-

import os
import re
import codecs
from setuptools import setup, find_packages
from setuptools.command.test import test as orig_test


# Note: the name of the class is used as the name of the command on the console when the
# help text is printed, this is why I've used "test" as a class name.
class test(orig_test):
    # Removed the options of the original class: --test-module, --test-suite, --test-runner
    user_options = [
        ('verbosity=', 'v', 'Verbosity level: 0=minimal output, 1=normal output, '
         '2=verbose output, 3=very verbose output'),
        ('failfast', None, 'Tells Django to stop running the test suite after first failed test.'),
        ('reverse', 'r', 'Reverses test cases order.'),
    ]
    # We ask the arg parser of the command to pass all args to us.
    command_consumes_arguments = True

    def initialize_options(self):
        orig_test.initialize_options(self)
        self.verbosity = None
        self.failfast = None
        self.reverse = None
        # self.args is needed because of the above "command_consumes_arguments" class attribute.
        self.args = None


script_dir = os.path.dirname(os.path.abspath(__file__))


def find_version(*path):
    with codecs.open(os.path.join(script_dir, *path), 'r', 'utf8') as f:
        contents = f.read()

    # The version line must have the form
    # version_info = (X, Y, Z)
    m = re.search(
        r'^version_info\s*=\s*\(\s*(?P<v0>\d+)\s*,\s*(?P<v1>\d+)\s*,\s*(?P<v2>\d+)\s*\)\s*$',
        contents,
        re.MULTILINE,
    )
    if m:
        return '%s.%s.%s' % (m.group('v0'), m.group('v1'), m.group('v2'))
    raise RuntimeError('Unable to determine package version.')


with codecs.open(os.path.join(script_dir, 'README.rst'), 'r', 'utf8') as f:
    long_description = f.read()


setup(
    name='django-universal-view-decorator',
    version=find_version('src', 'django_universal_view_decorator', '__init__.py'),
    description='Smart view class (CBV) decoration',
    long_description=long_description,

    url='https://github.com/pasztorpisti/django-universal-view-decorator',

    author='István Pásztor',
    author_email='pasztorpisti@gmail.com',

    license='MIT',

    classifiers=[
        'License :: OSI Approved :: MIT License',

        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Framework :: Django',

        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],

    keywords='django universal view class decorator',
    packages=find_packages('src'),
    package_dir={'': 'src'},

    test_suite='setup_test_suite.SetupTestSuite',
    tests_require=['django==1.11.29', 'mock'],
    cmdclass={'test': test},
)

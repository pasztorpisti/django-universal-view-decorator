#!/usr/bin/env python

# There is another way to run the tests and that method handles the test dependencies:
# $ setup.py test [options]
#
# This script doesn't handle the dependencies (you have to install them manually) but
# running this is ways faster than "setup.py test". For local dev testing this is perfect.

import os
import sys

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv[:1] + ['test'] + sys.argv[1:])

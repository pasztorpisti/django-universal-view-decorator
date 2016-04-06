#!/usr/bin/env python

# This is a very simple minimalistic script so I keep it but this is not the preferred way to run the tests.
# The "setup.py test [options]" command should be used instead because that handles the test dependencies.

import os
import sys

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.settings')
    from django.core.management import execute_from_command_line
    execute_from_command_line(sys.argv[:1] + ['test'] + sys.argv[1:])

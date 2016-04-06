import os
import sys
import argparse
from unittest import TestSuite
import django
# supporting only django>=1.8
from django.test.runner import DiscoverRunner


class SetupTestSuite(TestSuite):
    def __init__(self):
        self.args = args = self._parse_args()

        os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.settings'
        django.setup()

        self.test_runner = DiscoverRunner(failfast=args.failfast, reverse=args.reverse, pattern=args.pattern)
        tests = self.test_runner.build_suite(test_labels=args.test_labels)
        super(SetupTestSuite, self).__init__(tests=tests)

        self.test_runner.setup_test_environment()
        self.old_config = self.test_runner.setup_databases()

    def run(self, result, *args, **kwargs):
        result.failfast = self.args.failfast
        result = super(SetupTestSuite, self).run(result, *args, **kwargs)
        self.test_runner.teardown_databases(self.old_config)
        self.test_runner.teardown_test_environment()
        return result

    @staticmethod
    def _parse_args():
        parser = argparse.ArgumentParser()
        parser.add_argument('-v', '--verbosity', type=int, choices=(0, 1, 2, 3), default=1,
                            help='Verbosity level; 0=minimal output, 1=normal output, '
                                 '2=verbose output, 3=very verbose output')
        parser.add_argument('--failfast', action='store_const', const=True, default=False,
                            help='Tells Django to stop running the test suite after first failed test.')
        parser.add_argument('-r', '--reverse', action='store_const', const=True, default=False,
                            help='Reverses test cases order.')
        parser.add_argument('-p', '--pattern', default=None, help='The test matching pattern. Defaults to test*.py.')
        parser.add_argument('test_labels', nargs='*')

        # FIXME: currently the "test" command of setup.py exits with failure if we try to pass the above
        # args on the commandline. For this reason this code is untested. We need a hack-around for this.
        args = parser.parse_args(sys.argv[2:])
        args.test_labels = args.test_labels or None
        return args

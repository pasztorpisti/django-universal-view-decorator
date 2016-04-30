
CHANGES
=======


v0.1.0
------

*Release date: 2016-05-01*

- Changed the default decorator_duplicate_priority to zero (from ``-sys.maxsize``).
- Replaced the original bloated README.rst with a simple short version.


v0.0.3-beta
-----------

*Release date: 2016-04-12*

- Moved the library sources into an ``src`` subdir in the package.
- Fixed setup.py: not including the ``tests`` package in the installation.


v0.0.2-beta
-----------

*Release date: 2016-04-07*

- Added the ``universal_view_decorator_with_args`` wrapper to be able to use legacy decorators with view classes
  and view class methods.
- Removed ``view_class_decorator`` and ``view_routine_decorator`` from the public interface of the library.
  You should use ``universal_view_decorator`` or ``universal_view_decorator_with_args`` that combines the features
  of the removed decorators.
- Added this CHANGES.rst file.
- Improved the contents of the half-ready README.rst.


v0.0.1-beta
-----------

*Release date: 2016-04-06*

First working version on pypi. Minor adjustments to the initial version to get it


v0.0.0-beta
-----------

*Release date: 2016-04-06*

First "working" version.

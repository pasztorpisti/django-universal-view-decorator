# -*- coding: utf-8 -*-

from .decorators.universal_view_decorator import universal_view_decorator
from .decorators.view_decorator_base import ViewDecoratorBase


__all__ = ['universal_view_decorator', 'ViewDecoratorBase']


# version_info[0]: Increase in case of large milestones/releases.
# version_info[1]: Increase this and zero out version_info[2] if you have explicitly modified
#                  a previously existing behavior/interface.
#                  If the behavior of an existing feature changes as a result of a bugfix
#                  and the new (bugfixed) behavior is that meets the expectations of the
#                  previous interface documentation then you shouldn't increase this, in that
#                  case increase only version_info[2].
# version_info[2]: Increase in case of bugfixes. Also use this if you added new features
#                  without modifying the behavior of the previously existing ones.
version_info = (0, 0, 1)
__version__ = '.'.join(str(n) for n in version_info)
__author__ = 'István Pásztor'
__license__ = 'MIT'

# vim: set encoding=utf-8 et sw=4 sts=4 :

from formencode import Invalid
from formencode.validators import *
from formencode.compound import *

from pymin.item import Item
from pymin.validatedclass import Field

class UpOneOf(OneOf):
    """
    Same as :class:`OneOf` but values are uppercased before validation.

    Examples::

        >>> uoo = UpOneOf(['A', 'B', 'C'])
        >>> uoo.to_python('a')
        'A'
        >>> uoo.to_python('B')
        'B'
        >>> uoo.to_python('x')
        Traceback (most recent call last):
            ...
        Invalid: Value must be one of: A; B; C (not 'X')
    """

    def _to_python(self, value, state):
        return value.upper()


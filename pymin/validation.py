# vim: set encoding=utf-8 et sw=4 sts=4 :

from formencode import Invalid
from formencode.validators import *
from formencode.compound import *

from pymin.item import Item
from pymin.validatedclass import Field

class UpOneOf(OneOf):
    "Same as :class:`OneOf` but values are uppercased before validation."
    def validate_python(self, value, state):
        return OneOf.validate_python(self, value.upper(), state)


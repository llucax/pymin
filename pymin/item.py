# vim: set et sts=4 sw=4 encoding=utf-8 :

r"Simple module that provides a validated and sequenced Item."

__all__ = ('Item',)

from pymin.seqtools import Sequence
from pymin.validatedclass import ValidatedClass

class Item(ValidatedClass, Sequence):
    r"""Item() -> Item object

    Utility class to inherit from to get validation and sequence behaviour.

    Please see pymin.seqtools and pymin.validatedclass modules help for
    more details.
    """

    def as_tuple(self):
        r"""as_tuple() -> tuple - Return tuple representing the object.

        The tuple returned preserves the validated fields declaration order.
        """
        return tuple([getattr(self, n) for n in self.validated_fields])


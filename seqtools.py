# vim: set encoding=utf-8 et sw=4 sts=4 :

r"""
Sequence utilities.

This module provides some tools to ease working with sequences.
"""

class Sequence:
    r"""Sequence() -> Sequence instance.

    This is an abstract class to ease the implementation of sequences. You can
    inherit your objects from this class and implement just a method called
    as_tuple() which returns a tuple representation of the object.

    Example:

    >>> class A(Sequence):
    >>>     def __init__(self):
    >>>         self.a = 1
    >>>         self.b = 2
    >>>     def as_tuple(self):
    >>>         return (self.a, self.b)
    >>> for i in A():
    >>>     print i
    >>> print A()[1]
    """

    def __iter__(self):
        r"iter(obj) -> iterator object :: Get iterator."
        for i in self.as_tuple():
            yield i

    def __len__(self):
        r"len(obj) -> int :: Get object length."
        return len(self.as_tuple())

    def __getitem__(self, i):
        r"obj[i] -> object :: Get item with the index i."
        return self.as_tuple()[i]

    def __repr__(self):
        return '%s%r' % (self.__class__.__name__, self.as_tuple())

def as_tuple(obj):
    if isinstance(obj, basestring):
        return (obj,)
    if hasattr(obj, 'items'):
        return tuple(obj.items())
    if hasattr(obj, '__iter__'):
        return tuple(obj)
    return (obj,)

def as_table(obj):
    obj = as_tuple(obj)
    for i in obj:
        if isinstance(i, basestring):
            return (obj,)
        if hasattr(i, '__iter__'):
            return obj
        return (obj,)


if __name__ == '__main__':

    class A(Sequence):
        def __init__(self):
            self.a = 1
            self.b = 2
        def as_tuple(self):
            return (self.a, self.b)

    class B:
        def __repr__(self):
            return 'B()'

    for i in A():
        print i

    print A()[1]

    for f in (as_tuple, as_table):

        print f.__name__

        print f(A())

        print f("hello")

        print f([1,2,3])

        print f([[1,2,3],[6,7,8]])

        print f(B())

        print f(dict(a=1, b=2))


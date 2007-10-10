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

    def __unicode__(self):
        return u'%s%r' % (self.__class__.__name__, self.as_tuple())

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __repr__(self):
        return str(self)

def as_tuple(obj):
    r"""as_tuple(obj) -> tuple :: Convert objects to tuple.

    This function returns a tuple for any object. If the object is
    a string or any non-sequence object, it returns a tuple with the
    single value. If the object is a sequece or a generator, it returns
    the conversion to a tuple of it.

    Example:

    >>> print f("hello")
    ('hello',)
    >>> print f([1,2,3])
    (1, 2, 3)
    >>> print f([[1,2,3],[6,7,8]])
    ([1, 2, 3], [6, 7, 8])
    >>> print f(dict(a=1, b=2))
    (('a', 1), ('b', 2))
    """
    if isinstance(obj, basestring):
        return (obj,)
    if hasattr(obj, 'items'):
        return tuple(obj.items())
    if hasattr(obj, '__iter__'):
        return tuple(obj)
    return (obj,)

def as_table(obj):
    r"""as_table(obj) -> tuple of tuples :: Convert objects to tuple of tuples.

    This function returns a tuple of tuples for any object.

    Example:

    >>> print f("hello")
    (('hello',),)
    >>> print f([1,2,3])
    ((1, 2, 3),)
    >>> print f([[1,2,3],[6,7,8]])
    ([1, 2, 3], [6, 7, 8])
    >>> print f(dict(a=1, b=2))
    (('a', 1), ('b', 2))
    """
    obj = as_tuple(obj)
    for i in obj:
        if isinstance(i, basestring):
            return (obj,)
        if hasattr(i, '__iter__'):
            return obj
        return (obj,)
    else:
        return ((),) # empty table


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

        print f([])


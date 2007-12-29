# vim: set encoding=utf-8 et sw=4 sts=4 :

from pymin import ucsv
from pymin import seqtools

r"UTF-8 encoded CSV serializer."

def serialize(obj, output=None):
    r"""serialize(obj[, output]) -> None/unicode string

    Serialize the object obj to a UTF-8 encoded CSV string. If output
    is not None, it's used as a file object to store the string. If it's
    None, the string is returned.

    obj is expected to be a sequence of sequences, i.e. a list of rows.
    """
    stringio = False
    if output is None:
        stringio = True
        try:
            from cStringIO import StringIO
        except ImportError:
            from StringIO import StringIO
        output = StringIO()
    ucsv.writer(output).writerows(seqtools.as_table(obj))
    if stringio:
        return output.getvalue()


if __name__ == '__main__':

    from pymin.seqtools import Sequence

    class Host(Sequence):
        r"""Host(name, ip, mac) -> Host instance :: Class representing a host.

        name - Host name, should be a fully qualified name, but no checks are done.
        ip - IP assigned to the hostname.
        mac - MAC address to associate to the hostname.
        """

        def __init__(self, name, ip, mac):
            r"Initialize Host object, see class documentation for details."
            self.name = name
            self.ip = ip
            self.mac = mac

        def as_tuple(self):
            return (self.name, self.ip, self.mac)

        def __unicode__(self):
            return u'no anda'

    print serialize(1)

    print serialize("lala")

    print serialize(u"lala")

    print serialize([1, 2])

    print serialize(["lala", "lala"])

    print serialize([u"lala", u"lala"])

    h = Host('name', 'ip', 'mac')
    print serialize(h)

    print serialize(dict(a=1, b=2))

    print serialize([[1, 2, 3], [7, 4, 2]])

    print serialize([["adfj", "jdfhk"], ["alskdjal", "1uas"]])

    print serialize([[u"adfj", u"jdfhk"], [u"alskdjal", u"1uas"]])

    print serialize([h, h])

    import sys
    print 'stdout:'
    serialize([h, h], sys.stdout)
    print

    for i in h: print i


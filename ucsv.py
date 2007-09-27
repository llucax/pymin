# vim: set encoding=utf-8 et sw=4 sts=4 :

import csv
import codecs
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

r"""
CSV parsing and writing supporting unicode and encodings.

This module is copied from Python 2.5 csv module documentation:
http://docs.python.org/lib/csv-examples.html

It's adapted to work, at least, on Python 2.4.
"""

class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")

class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self

class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        if hasattr(codecs, 'getincrementalencoder'):
            self.encoder = codecs.getincrementalencoder(encoding)()
        else:
            class E:
                def __init__(self, encoding):
                    self.encoding = encoding
                def encode(self, obj):
                    return codecs.encode(obj, encoding)
            self.encoder = E(encoding)

    def writerow(self, row):
        self.writer.writerow([unicode(s).encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

writer = UnicodeWriter

reader = UnicodeReader


if __name__ == '__main__':

    sio = StringIO()

    writer = writer(sio)
    writer.writerows([[u"adfj", u"ñjdfhk"], [u"áalskdjal", u"1uas"]])

    print sio.getvalue()

    sio.seek(0)

    for row in reader(sio):
        print row


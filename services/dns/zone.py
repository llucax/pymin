# vim: set encoding=utf-8 et sw=4 sts=4 :

# TODO documentation, validation

from pymin.seqtools import Sequence
from pymin.service.util import DictSubHandler

__all__ = ('DnsHandler',)


class Zone(Sequence):
    def __init__(self, name):
        self.name = name
        self.hosts = dict()
        self.mxs = dict()
        self.nss = dict()
        self._add = False
        self._update = False
        self._delete = False
    def as_tuple(self):
        return (self.name, self.hosts, self.mxs, self.nss)

class ZoneHandler(DictSubHandler):
    handler_help = u"Manage DNS zones"
    _cont_subhandler_attr = 'zones'
    _cont_subhandler_class = Zone


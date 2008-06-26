# vim: set encoding=utf-8 et sw=4 sts=4 :

# TODO documentation

from pymin.validation import Item, Field, FullyQualifiedHostName
from pymin.service.util import DictSubHandler

__all__ = ('DnsHandler',)


class Zone(Item):
    name = Field(FullyQualifiedHostName(not_empty=True))
    def __init__(self, *args, **kwargs):
        Item.__init__(self, *args, **kwargs)
        self.hosts = dict()
        self.mxs = dict()
        self.nss = dict()
        self._add = False
        self._update = False
        self._delete = False

class ZoneHandler(DictSubHandler):
    handler_help = u"Manage DNS zones"
    _cont_subhandler_attr = 'zones'
    _cont_subhandler_class = Zone


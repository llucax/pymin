# vim: set encoding=utf-8 et sw=4 sts=4 :

# TODO documentation

from pymin.validation import Item, Field, HostName, IPAddress
from pymin.service.util import DictComposedSubHandler

__all__ = ('HostHandler',)


class Host(Item):
    name = Field(HostName(not_empty=True))
    ip = Field(IPAddress(not_empty=True))

class HostHandler(DictComposedSubHandler):
    handler_help = u"Manage DNS hosts"
    _comp_subhandler_cont = 'zones'
    _comp_subhandler_attr = 'hosts'
    _comp_subhandler_class = Host


# vim: set encoding=utf-8 et sw=4 sts=4 :

from pymin.validation import Item, Field, Any, HostName, \
                             FullyQualifiedHostName, IPAddress, CIDR
from pymin.service.util import DictComposedSubHandler

__all__ = ('HostHandler',)


class Host(Item):
    name = Field(HostName(not_empty=True))
    address = Field(Any(HostName, FullyQualifiedHostName, IPAddress))
    subnet = Field(CIDR)

class HostHandler(DictComposedSubHandler):

    handler_help = u"Manage hosts for a vpn"
    _comp_subhandler_cont = 'vpns'
    _comp_subhandler_attr = 'hosts'
    _comp_subhandler_class = Host


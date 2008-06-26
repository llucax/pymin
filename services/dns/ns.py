# vim: set encoding=utf-8 et sw=4 sts=4 :

# TODO documentation

from pymin.validation import Item, Field, FullyQualifiedHostName
from pymin.service.util import DictComposedSubHandler

__all__ = ('NameServerHandler',)


class NameServer(Item):
    name = Field(FullyQualifiedHostName(not_empty=True))

class NameServerHandler(DictComposedSubHandler):
    handler_help = u"Manage DNS name servers (NS)"
    _comp_subhandler_cont = 'zones'
    _comp_subhandler_attr = 'nss'
    _comp_subhandler_class = NameServer


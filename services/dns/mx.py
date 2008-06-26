# vim: set encoding=utf-8 et sw=4 sts=4 :

# TODO documentation

from pymin.validation import Item, Field, FullyQualifiedHostName, UInt16
from pymin.service.util import DictComposedSubHandler

__all__ = ('MailExchangeHandler',)


class MailExchange(Item):
    mx = Field(FullyQualifiedHostName(not_empty=True))
    prio = Field(UInt16(not_empty=True))

class MailExchangeHandler(DictComposedSubHandler):
    handler_help = u"Manage DNS mail exchangers (MX)"
    _comp_subhandler_cont = 'zones'
    _comp_subhandler_attr = 'mxs'
    _comp_subhandler_class = MailExchange


# vim: set encoding=utf-8 et sw=4 sts=4 :

# TODO documentation, validation

from pymin.seqtools import Sequence
from pymin.service.util import DictComposedSubHandler

__all__ = ('MailExchangeHandler',)


class MailExchange(Sequence):
    def __init__(self, mx, prio):
        self.mx = mx
        self.prio = prio
    def update(self, prio=None):
        if prio is not None: self.prio = prio
    def as_tuple(self):
        return (self.mx, self.prio)

class MailExchangeHandler(DictComposedSubHandler):
    handler_help = u"Manage DNS mail exchangers (MX)"
    _comp_subhandler_cont = 'zones'
    _comp_subhandler_attr = 'mxs'
    _comp_subhandler_class = MailExchange


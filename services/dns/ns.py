# vim: set encoding=utf-8 et sw=4 sts=4 :

# TODO documentation, validation

from pymin.seqtools import Sequence
from pymin.service.util import DictComposedSubHandler

__all__ = ('NameServerHandler',)


class NameServer(Sequence):
    def __init__(self, name):
        self.name = name
    def as_tuple(self):
        return (self.name,)

class NameServerHandler(DictComposedSubHandler):
    handler_help = u"Manage DNS name servers (NS)"
    _comp_subhandler_cont = 'zones'
    _comp_subhandler_attr = 'nss'
    _comp_subhandler_class = NameServer


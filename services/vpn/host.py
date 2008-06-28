# vim: set encoding=utf-8 et sw=4 sts=4 :

from pymin.seqtools import Sequence
from pymin.service.util import DictComposedSubHandler

__all__ = ('HostHandler',)


class Host(Sequence):
    def __init__(self, name, address, subnet, public_key):
        self.name = name
        self.address = address
        self.subnet = subnet
        self.public_key = public_key
        self._delete = False

    def as_tuple(self):
        return(self.name, self.address, self.subnet, self.public_key)

class HostHandler(DictComposedSubHandler):

    handler_help = u"Manage hosts for a vpn"
    _comp_subhandler_cont = 'vpns'
    _comp_subhandler_attr = 'hosts'
    _comp_subhandler_class = Host


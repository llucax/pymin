# vim: set encoding=utf-8 et sw=4 sts=4 :

from pymin.seqtools import Sequence
from pymin.service.util import DictComposedSubHandler

__all__ = ('HostHandler',)


class Host(Sequence):
    def __init__(self, vpn_src, ip, vpn_src_net, key):
        self.name = vpn_src
        self.ip = ip
        self.src_net = vpn_src_net
        self.pub_key = key
        self._delete = False

    def as_tuple(self):
        return(self.name, self.ip, self.src_net, self.pub_key)

class HostHandler(DictComposedSubHandler):

    handler_help = u"Manage hosts for a vpn"
    _comp_subhandler_cont = 'vpns'
    _comp_subhandler_attr = 'hosts'
    _comp_subhandler_class = Host


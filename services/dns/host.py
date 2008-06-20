# vim: set encoding=utf-8 et sw=4 sts=4 :

# TODO documentation, validation

from pymin.seqtools import Sequence
from pymin.service.util import DictComposedSubHandler

__all__ = ('HostHandler',)

class Host(Sequence):
    def __init__(self, name, ip):
        self.name = name
        self.ip = ip
    def update(self, ip=None):
        if ip is not None: self.ip = ip
    def as_tuple(self):
        return (self.name, self.ip)

class HostHandler(DictComposedSubHandler):
    handler_help = u"Manage DNS hosts"
    _comp_subhandler_cont = 'zones'
    _comp_subhandler_attr = 'hosts'
    _comp_subhandler_class = Host


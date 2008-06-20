# vim: set encoding=utf-8 et sw=4 sts=4 :

from pymin.seqtools import Sequence
from pymin.dispatcher import handler
from pymin.service.util import ContainerNotFoundError, ListSubHandler

__all__ = ('HopHandler',)


class Hop(Sequence):

    def __init__(self, gateway, device):
        self.gateway = gateway
        self.device = device

    def as_tuple(self):
        return (self.gateway, self.device)

    def __cmp__(self, other):
        if self.gateway == other.gateway \
                and self.device == other.device:
            return 0
        return cmp(id(self), id(other))

class HopHandler(ListSubHandler):
    handler_help = u"Manage IP hops"
    _cont_subhandler_attr = 'hops'
    _cont_subhandler_class = Hop

    @handler('Add a hop: add <device> <gateway>')
    def add(self, dev, gw):
        if not dev in self.parent.devices:
            raise ContainerNotFoundError(device)
        return ListSubHandler.add(self, dev, gw)


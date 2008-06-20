# vim: set encoding=utf-8 et sw=4 sts=4 :

from pymin.seqtools import Sequence
from pymin.dispatcher import handler
from pymin.service.util import SubHandler, ContainerNotFoundError, \
                               ItemAlreadyExistsError

__all__ = ('HostHandler',)


class Host(Sequence):

    def __init__(self, ip):
        self.ip = ip

    def as_tuple(self):
        return (self.ip)

    def __cmp__(self, other):
        if self.ip == other.ip:
            return 0
        return cmp(id(self), id(other))


class HostHandler(SubHandler):

    def __init__(self, parent):
        self.parent = parent

    @handler('Adds a host to a class : add <device> <class id> <ip>')
    def add(self, dev, cid, ip):
        if not dev in self.parent.devices:
            raise ContainerNotFoundError(dev)

        if not cid in self.parent.devices[dev].classes:
            raise ContainerNotFoundError(cid)

        try:
            self.parent.devices[dev].classes[cid].hosts[ip] = Host(ip)
        except ValueError:
            raise ItemAlreadyExistsError(h  + ' -> ' + dev)

    @handler(u'Lists hosts : list <dev> <class id>')
    def list(self, dev, cid):
        try:
            k = self.parent.devices[dev].classes[cid].hosts.keys()
        except KeyError:
            k = dict()
        return k


# vim: set encoding=utf-8 et sw=4 sts=4 :

from pymin.seqtools import Sequence
from pymin.dispatcher import handler
from pymin.service.util import SubHandler, ContainerNotFoundError, \
                               ItemNotFoundError, ItemAlreadyExistsError

__all__ = ('ClassHandler',)


class Class(Sequence):

    def __init__(self, cid, rate=None):
        self.cid = cid
        self.rate = rate
        self.hosts = dict()

    def as_tuple(self):
        return (self.cid, self.rate)

    def __cmp__(self, other):
        if self.cid == other.cid:
            return 0
        return cmp(id(self), id(other))


class ClassHandler(SubHandler):

    def __init__(self, parent):
        self.parent = parent

    @handler('Adds a class : add <id> <device> <rate>')
    def add(self, dev, cid, rate):
        if not dev in self.parent.devices:
            raise ContainerNotFoundError(dev)

        try:
            self.parent.devices[dev].classes[cid] = Class(cid, rate)
        except ValueError:
            raise ItemAlreadyExistsError(cid  + ' -> ' + dev)

    @handler(u'Deletes a class : delete <id> <device>')
    def delete(self, dev, cid):
        if not dev in self.parent.devices:
            raise ContainerNotFoundError(dev)

        try:
            del self.parent.devices[dev].classes[cid]
        except KeyError:
            raise ItemNotFoundError(cid + ' -> ' + dev)

    @handler(u'Lists classes : list <dev>')
    def list(self, dev):
        try:
            k = self.parent.devices[dev].classes.items()
        except KeyError:
            k = dict()
        return k


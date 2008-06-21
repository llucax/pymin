# vim: set encoding=utf-8 et sw=4 sts=4 :

from pymin.seqtools import Sequence
from pymin.service.util import DictSubHandler

__all__ = ('HostHandler',)


class Host(Sequence):
    def __init__(self,ip):
        self.ip = ip
    def as_tuple(self):
        return (self.ip,)

class HostHandler(DictSubHandler):

    handler_help = u"Manage proxy hosts"

    _cont_subhandler_attr = 'hosts'
    _cont_subhandler_class = Host


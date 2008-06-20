# vim: set encoding=utf-8 et sw=4 sts=4 :

from pymin.seqtools import Sequence
from pymin.service.util import DictSubHandler

__all__ = ('ConnectionHandler',)


class Connection(Sequence):

    def __init__(self, name, username, password, type, **kw):
        self.name = name
        self.username = username
        self.password = password
        self.type = type
        self._running = False
        if type == 'OE':
            if not 'device' in kw:
                raise ConnectionError('Bad arguments for type=OE')
            self.device = kw['device']
        elif type == 'TUNNEL':
            if not 'server' in kw:
                raise ConnectionError('Bad arguments for type=TUNNEL')
            self.server = kw['server']
            self.username = self.username.replace('\\','\\\\')
        elif type == 'PPP':
            if not 'device' in kw:
                raise ConnectionError('Bad arguments for type=PPP')
            self.device = kw['device']
        else:
            raise ConnectionError('Bad arguments, unknown or unspecified type')

    def as_tuple(self):
        if self.type == 'TUNNEL':
            return (self.name, self.username, self.password, self.type, self.server)
        elif self.type == 'PPP' or self.type == 'OE':
            return (self.name, self.username, self.password, self.type, self.device)

    def update(self, device=None, username=None, password=None):
        if device is not None:
            self.device = device
        if username is not None:
            self.username = username
        if password is not None:
            self.password = password


class ConnectionHandler(DictSubHandler):

    handler_help = u"Manages connections for the ppp service"

    _cont_subhandler_attr = 'conns'
    _cont_subhandler_class = Connection


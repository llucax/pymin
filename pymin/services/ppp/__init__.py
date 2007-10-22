# vim: set encoding=utf-8 et sw=4 sts=4 :

from os import path

from pymin.seqtools import Sequence
from pymin.dispatcher import Handler, handler, HandlerError
from pymin.services.util import Restorable, ConfigWriter \
                                ,TransactionalHandler, DictSubHandler, call

__ALL__ = ('PppHandler',)

class ConnectionError(HandlerError, KeyError):
    r"""
    ConnectionError(hostname) -> ConnectionError instance

    This is the base exception for all connection related errors.
    """

    def __init__(self, connection):
        r"Initialize the object. See class documentation for more info."
        self.message = u'Connection error: "%s"' % connection

class ConnectionNotFoundError(ConnectionError):
    def __init__(self, connection):
        r"Initialize the object. See class documentation for more info."
        self.message = u'Connection not found error: "%s"' % connection

class Connection(Sequence):

    def __init__(self, name, username, password, type, **kw):
        self.name = name
        self.username = username
        self.password = password
        self.type = type
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

class PppHandler(Restorable, ConfigWriter, TransactionalHandler):

    handler_help = u"Manage ppp service"

    _persistent_attrs = ['conns']

    _restorable_defaults = dict(
        conns  = dict(),
    )

    _config_writer_files = ('options.X','pap-secrets','chap-secrets','nameX')
    _config_writer_tpl_dir = path.join(path.dirname(__file__), 'templates')

    def __init__(self, pickle_dir='.', config_dir='.'):
        r"Initialize Ppphandler object, see class documentation for details."
        self._persistent_dir = pickle_dir
        self._config_writer_cfg_dir = config_dir
        self._config_build_templates()
        self._restore()
        self.conn = ConnectionHandler(self)

    @handler('Starts the service')
    def start(self, name):
        if name in self.conns:
            #call(('pon', name))
            print ('pon', name)
        else:
            raise ConnectionNotFoundError(name)

    @handler('Stops the service')
    def stop(self, name):
        if name in self.conns:
            #call(('poff', name))
            print ('poff', name)
        else:
            raise ConnectionNotFoundError(name)

    @handler('Reloads the service')
    def reload(self):
        for conn in self.conns.values():
            self.stop(conn.name)
            self.start(conn.name)

    def _write_config(self):
        r"_write_config() -> None :: Generate all the configuration files."
        #guardo los pass que van el pap-secrets
        vars_pap = dict()
        for conn in self.conns.values():
            if conn.type == 'OE' or conn.type == 'PPP':
                vars_pap[conn.name] = conn
        vars = dict(conns=vars_pap)
        self._write_single_config('pap-secrets','pap-secrets',vars)
        #guardo los pass que van el chap-secrets
        vars_chap = dict()
        for conn in self.conns.values():
            if conn.type == 'TUNNEL' :
                vars_chap[conn.name] = conn
        vars = dict(conns=vars_chap)
        self._write_single_config('chap-secrets','chap-secrets',vars)
        #guard las conns
        for conn in self.conns.values():
            vars = dict(conn=conn)
            self._write_single_config('nameX',conn.name, vars)
            self._write_single_config('options.X','options.' + conn.name, vars)


if __name__ == '__main__':
    p = PppHandler()
    p.conn.add('ppp_c','nico','nico',type='PPP',device='tty0')
    p.conn.add('pppoe_c','fede','fede',type='OE',device='tty1')
    p.conn.add('ppptunnel_c','dominio\luca','luca',type='TUNNEL',server='192.168.0.23')
    p.commit()
    print p.conn.list()
    print p.conn.show()

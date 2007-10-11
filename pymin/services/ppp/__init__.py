# vim: set encoding=utf-8 et sw=4 sts=4 :

from os import path

from pymin.seqtools import Sequence
from pymin.dispatcher import Handler, handler, HandlerError
from pymin.services.util import Restorable, ConfigWriter \
                                ,TransactionalHandler, DictSubHandler, call

__ALL__ = ('PppHandler')

class Error(HandlerError):
    r"""
    Error(command) -> Error instance :: Base ConnectionHandler exception class.

    All exceptions raised by the ConnectionHandler inherits from this one, so you can
    easily catch any ConnectionHandler exception.

    message - A descriptive error message.
    """
    pass

class ConnectionError(Error, KeyError):
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

    def __init__(self, name, dev, username=None, password=None):
        self.name = name
        self.dev = dev
        self.username = username
        self.password = password

    def as_tuple(self):
        return (self.name, self.dev, self.username, self.password)

    def update(self, dev=None, username=None, password=None):
        if dev is not None:
            self.dev = dev
        if username is not None:
            self.username = username
        if password is not None:
            self.password = password


class ConnectionHandler(DictSubHandler):

    handler_help = u"Manages connections for the ppp service"

    _dict_subhandler_attr = 'conns'
    _dict_subhandler_class = Connection

class PppHandler(Restorable, ConfigWriter, TransactionalHandler):

    handler_help = u"Manage ppp service"

    _persistent_attrs = ('conns')

    _restorable_defaults = dict(
        conns  = dict(),
    )

    _config_writer_files = ('options.X','pap-secrets','nameX')
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
        vars = dict(conns=self.conns)
        self._write_single_config('pap-secrets','pap-secrets',vars)
        for conn in self.conns.values():
            vars = dict(conn=conn)
            self._write_single_config('nameX',conn.name, vars)
            self._write_single_config('options.X','options.' + conn.name, vars)


if __name__ == '__main__':
    p = PppHandler()
    p.conn.add('test2','tty2','luca','luca')
    p.commit()
    print p.conn.list()
    print p.conn.show()
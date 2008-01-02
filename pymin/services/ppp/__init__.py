# vim: set encoding=utf-8 et sw=4 sts=4 :

import os
import subprocess
from os import path
from signal import SIGTERM
import logging ; log = logging.getLogger('pymin.services.ppp')

from pymin.seqtools import Sequence
from pymin.dispatcher import Handler, handler, HandlerError
from pymin.services.util import Restorable, ConfigWriter, ReloadHandler, \
                                TransactionalHandler, DictSubHandler, call

__all__ = ('PppHandler',)

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

class PppHandler(Restorable, ConfigWriter, ReloadHandler, TransactionalHandler):

    handler_help = u"Manage ppp service"

    _persistent_attrs = ['conns']

    _restorable_defaults = dict(
        conns  = dict(),
    )

    _config_writer_files = ('options.X','pap-secrets','chap-secrets','nameX')
    _config_writer_tpl_dir = path.join(path.dirname(__file__), 'templates')

    def __init__(self, pickle_dir='.', config_dir='.'):
        r"Initialize Ppphandler object, see class documentation for details."
        log.debug(u'PppHandler(%r, %r)', pickle_dir, config_dir)
        self._persistent_dir = pickle_dir
        self._config_writer_cfg_dir = config_dir
        self._config_build_templates()
        self._restore()
        log.debug(u'PppHandler(): restoring connections...')
        for conn in self.conns.values():
            if conn._running:
                log.debug(u'PppHandler(): starting connection %r', conn.name)
                conn._running = False
                self.start(conn.name)
        self.conn = ConnectionHandler(self)

    @handler(u'Start one or all the connections.')
    def start(self, name=None):
        log.debug(u'PppHandler.start(%r)', name)
        names = [name]
        if name is None:
            names = self.conns.keys()
        for name in names:
            if name in self.conns:
                if not self.conns[name]._running:
                    log.debug(u'PppHandler.start: starting connection %r', name)
                    call(('pppd', 'call', name))
                    self.conns[name]._running = True
                    self._dump_attr('conns')
            else:
                log.debug(u'PppHandler.start: connection not found')
                raise ConnectionNotFoundError(name)

    @handler(u'Stop one or all the connections.')
    def stop(self, name=None):
        log.debug(u'PppHandler.stop(%r)', name)
        names = [name]
        names = [name]
        if name is None:
            names = self.conns.keys()
        for name in names:
            if name in self.conns:
                if self.conns[name]._running:
                    pid_file = '/var/run/ppp-' + name + '.pid'
                    log.debug(u'PppHandler.stop: getting pid from %r', pid_file)
                    if path.exists(pid_file):
                        pid = file(pid_file).readline()
                        pid = int(pid.strip())
                        try:
                            log.debug(u'PppHandler.stop: killing pid %r', pid)
                            os.kill(pid, SIGTERM)
                        except OSError, e:
                            log.debug(u'PppHandler.stop: error killing: %r', e)
                    else:
                        log.debug(u'PppHandler.stop: pid file not found')
                    self.conns[name]._running = False
                    self._dump_attr('conns')
                else:
                    log.debug(u'PppHandler.stop: connection not running')
            else:
                log.debug(u'PppHandler.stop: connection not found')
                raise ConnectionNotFoundError(name)

    @handler(u'Restart one or all the connections (even disconnected ones).')
    def restart(self, name=None):
        log.debug(u'PppHandler.restart(%r)', name)
        names = [name]
        if name is None:
            names = self.conns.keys()
        for name in names:
            self.stop(name)
            self.start(name)

    @handler(u'Restart only one or all the already running connections.')
    def reload(self, name=None):
        r"reload() -> None :: Reload the configuration of the service."
        log.debug(u'PppHandler.reload(%r)', name)
        names = [name]
        if name is None:
            names = self.conns.keys()
        for name in names:
            if self.conns[name]._running:
                self.stop(name)
                self.start(name)

    @handler(u'Tell if the service is running.')
    def running(self, name=None):
        r"reload() -> None :: Reload the configuration of the service."
        log.debug(u'PppHandler.running(%r)', name)
        if name is None:
            return [c.name for c in self.conns.values() if c._running]
        if name in self.conns:
            return int(self.conns[name]._running)
        else:
            log.debug(u'PppHandler.running: connection not found')
            raise ConnectionNotFoundError(name)

    def handle_timer(self):
        log.debug(u'PppHandler.handle_timer()')
        for c in self.conns.values():
            log.debug(u'PppHandler.handle_timer: processing connection %r', c)
            p = subprocess.Popen(('pgrep', '-f', 'pppd call ' + c.name),
                                    stdout=subprocess.PIPE)
            pid = p.communicate()[0]
            if p.returncode == 0 and len(pid) > 0:
                log.debug(u'PppHandler.handle_timer: pid present, running')
                c._running = True
            else:
                log.debug(u'PppHandler.handle_timer: pid absent, NOT running')
                c._running = False

    def _write_config(self):
        r"_write_config() -> None :: Generate all the configuration files."
        log.debug(u'PppHandler._write_config()')
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

    logging.basicConfig(
        level   = logging.DEBUG,
        format  = '%(asctime)s %(levelname)-8s %(message)s',
        datefmt = '%H:%M:%S',
    )

    p = PppHandler()
    p.conn.add('ppp_c','nico','nico',type='PPP',device='tty0')
    p.conn.add('pppoe_c','fede','fede',type='OE',device='tty1')
    p.conn.add('ppptunnel_c','dominio\luca','luca',type='TUNNEL',server='192.168.0.23')
    p.commit()
    print p.conn.list()
    print p.conn.show()


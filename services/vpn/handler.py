# vim: set encoding=utf-8 et sw=4 sts=4 :

import os
import errno
import signal
from os import path
import logging ; log = logging.getLogger('pymin.services.vpn')

from pymin.seqtools import Sequence
from pymin.dispatcher import handler, HandlerError
from pymin.service.util import Restorable, ConfigWriter, InitdHandler, \
                               TransactionalHandler, DictSubHandler, \
                               call, ExecutionError

from host import HostHandler

__all__ = ('VpnHandler',)


class Vpn(Sequence):
    def __init__(self, name, connect_to, local_ip, mask,
                 public_key=None, private_key=None):
        self.name = name
        self.connect_to = connect_to
        self.local_ip = local_ip
        self.mask = mask
        self.public_key = public_key
        self.private_key = private_key
        self.hosts = dict()
        self._delete = False

    def as_tuple(self):
        return (self.name, self.connect_to, self.local_ip, self.mask,
                self.public_key, self.private_key)

    def update(self, connect_to=None, local_ip=None, mask=None):
        if connect_to is not None:
            self.connect_to = connect_to
        if local_ip is not None:
            self.local_ip = local_ip
        if mask is not None:
            self.mask = mask


class VpnHandler(Restorable, ConfigWriter,
                   TransactionalHandler, DictSubHandler):

    handler_help = u"Manage vpn service"

    _cont_subhandler_attr = 'vpns'
    _cont_subhandler_class = Vpn

    _persistent_attrs = ('vpns','hosts')

    _restorable_defaults = dict(
            vpns = dict(),
            hosts = dict(),
    )

    _config_writer_files = ('tinc.conf','tinc-up','host')
    _config_writer_tpl_dir = path.join(path.dirname(__file__), 'templates')

    def __init__(self,  pickle_dir='.', config_dir='/etc/tinc'):
        log.debug(u'VpnHandler(%r, %r)', pickle_dir, config_dir)
        DictSubHandler.__init__(self, self)
        self._config_writer_cfg_dir = config_dir
        self._persistent_dir = pickle_dir
        self._config_build_templates()
        self._restore()
        self.host = HostHandler(self)

    @handler('usage: start <vpn_name>')
    def start(self, net_name):
        log.debug(u'VpnHandler.start(%r)', net_name)
        if net_name in self.vpns:
            call(('tincd','--net=' + net_name))

    @handler('usage: stop <vpn_name>')
    def stop(self, net_name):
        log.debug(u'VpnHandler.stop(%r)', net_name)
        if net_name in self.vpns:
            pid_file = '/var/run/tinc.' + net_name + '.pid'
            log.debug(u'VpnHandler.stop: getting pid from %r', pid_file)
            if path.exists(pid_file):
                pid = file(pid_file).readline()
                pid = int(pid.strip())
                try:
                    log.debug(u'VpnHandler.stop: killing pid %r', pid)
                    os.kill(pid, signal.SIGTERM)
                except OSError:
                    log.debug(u'VpnHandler.stop: error killing: %r', e)
            else:
                log.debug(u'VpnHandler.stop: pid file not found')

    def _write_config(self):
        log.debug(u'VpnHandler._write_config()')
        for v in self.vpns.values():
            log.debug(u'VpnHandler._write_config: processing %r', v)
            #chek whether it's been created or not.
            if not v._delete:
                if v.public_key is None:
                    log.debug(u'VpnHandler._write_config: new VPN, generating '
                                'key...')
                    try:
                        log.debug(u'VpnHandler._write_config: creating dir %r',
                                    path.join(self._config_writer_cfg_dir,
                                                v.name, 'hosts'))
                        #first create the directory for the vpn
                        try:
                            os.makedirs(path.join(self._config_writer_cfg_dir,
                                                  v.name, 'hosts'))
                        except (IOError, OSError), e:
                            if e.errno != errno.EEXIST:
                                raise HandlerError(u"Can't create VPN config "
                                                   "directory '%s' (%s)'"
                                                    % (e.filename, e.strerror))
                        #this command should generate 2 files inside the vpn
                        #dir, one rsa_key.priv and one rsa_key.pub
                        #for some reason debian does not work like this
                        # FIXME if the < /dev/null works, is magic!
                        log.debug(u'VpnHandler._write_config: creating key...')
                        call(('tincd', '-n', v.name, '-K', '<', '/dev/null'))
                        #open the created files and load the keys
                        try:
                            f = file(path.join(self._config_writer_cfg_dir,
                                               v.name, 'rsa_key.pub'),
                                     'r')
                            pub = f.read()
                            f.close()
                        except (IOError, OSError), e:
                            raise HandlerError(u"Can't read VPN key '%s' (%s)'"
                                                % (e.filename, e.strerror))

                        v.public_key = pub
                        v.private_key = priv
                    except ExecutionError, e:
                        log.debug(u'VpnHandler._write_config: error executing '
                                    'the command: %r', e)

                self._write_single_config('tinc.conf',
                                path.join(v.name, 'tinc.conf'), dict(vpn=v))
                self._write_single_config('tinc-up',
                                path.join(v.name, 'tinc-up'), dict(vpn=v))
                for h in v.hosts.values():
                    if not h._delete:
                        self._write_single_config('host',
                                path.join(v.name, 'hosts', h.name),
                                dict(host=h))
                    else:
                        log.debug(u'VpnHandler._write_config: removing...')
                        try:
                            # FIXME use os.unlink()
                            call(('rm','-f',
                                    path.join(v.name, 'hosts', h.name)))
                            del v.hosts[h.name]
                        except ExecutionError, e:
                            log.debug(u'VpnHandler._write_config: error '
                                    'removing files: %r', e)
            else:
                #delete the vpn root at tinc dir
                if path.exists('/etc/tinc/' + v.name):
                    self.stop(v.name)
                    call(('rm','-rf','/etc/tinc/' + v.name))
                    del self.vpns[v.name]


if __name__ == '__main__':

    logging.basicConfig(
        level   = logging.DEBUG,
        format  = '%(asctime)s %(levelname)-8s %(message)s',
        datefmt = '%H:%M:%S',
    )

    v = VpnHandler('/tmp', '/tmp')
    v.add('prueba','sarasa','192.168.0.188','255.255.255.0')
    v.host.add('prueba', 'azazel' ,'192.168.0.77', '192.168.0.0',
                'kjdhfkbdskljvkjblkbjeslkjbvkljbselvslberjhbvslbevlhb')
    v.commit()


# vim: set encoding=utf-8 et sw=4 sts=4 :

import os
import errno
import signal
from os import path
import logging ; log = logging.getLogger('pymin.services.vpn')

from pymin.seqtools import Sequence
from pymin.dispatcher import Handler, handler, HandlerError
from pymin.service.util import Restorable, ConfigWriter, InitdHandler, \
                               TransactionalHandler, DictSubHandler, DictComposedSubHandler, call, ExecutionError

__all__ = ('VpnHandler', 'get_service')


def get_service(config):
    return VpnHandler(config.vpn.pickle_dir, config.vpn.config_dir)


class Host(Sequence):
    def __init__(self, vpn_src, ip, vpn_src_net, key):
        self.name = vpn_src
        self.ip = ip
        self.src_net = vpn_src_net
        self.pub_key = key
        self._delete = False

    def as_tuple(self):
        return(self.name, self.ip, self.src_net, self.pub_key)

class HostHandler(DictComposedSubHandler):

    handler_help = u"Manage hosts for a vpn"
    _comp_subhandler_cont = 'vpns'
    _comp_subhandler_attr = 'hosts'
    _comp_subhandler_class = Host


class Vpn(Sequence):
    def __init__(self, vpn_src, vpn_dst, vpn_src_ip, vpn_src_mask,
                    pub_key=None, priv_key=None):
        self.vpn_src = vpn_src
        self.vpn_dst = vpn_dst
        self.vpn_src_ip = vpn_src_ip
        self.vpn_src_mask = vpn_src_mask
        self.pub_key = pub_key
        self.priv_key = priv_key
        self.hosts = dict()
        self._delete = False

    def as_tuple(self):
        return(self.vpn_src, self.vpn_dst, self.vpn_src_ip, self.vpn_src_mask, self.pub_key, self.priv_key)

    def update(self, vpn_dst=None, vpn_src_ip=None, vpn_src_mask=None):
        if vpn_dst is not None:
            self.vpn_dst = vpn_dst
        if vpn_src_ip is not None:
            self.vpn_src_ip = vpn_src_ip
        if vpn_src_mask is not None:
            self.vpn_src_mask = vpn_src_mask


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
    def start(self, vpn_src):
        log.debug(u'VpnHandler.start(%r)', vpn_src)
        if vpn_src in self.vpns:
            call(('tincd','--net='+ vpn_src))

    @handler('usage: stop <vpn_name>')
    def stop(self, vpn_src):
        log.debug(u'VpnHandler.stop(%r)', vpn_src)
        if vpn_src in self.vpns:
            pid_file = '/var/run/tinc.' + vpn_src + '.pid'
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
                if v.pub_key is None:
                    log.debug(u'VpnHandler._write_config: new VPN, generating '
                                'key...')
                    try:
                        log.debug(u'VpnHandler._write_config: creating dir %r',
                                    path.join(self._config_writer_cfg_dir,
                                                v.vpn_src ,'hosts'))
                        #first create the directory for the vpn
                        try:
                            os.makedirs(path.join(self._config_writer_cfg_dir,
                                                  v.vpn_src, 'hosts'))
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
                        call(('tincd', '-n', v.vpn_src, '-K', '<', '/dev/null'))
                        #open the created files and load the keys
                        try:
                            f = file(path.join(self._config_writer_cfg_dir,
                                               v.vpn_src, 'rsa_key.pub'),
                                     'r')
                            pub = f.read()
                            f.close()
                        except (IOError, OSError), e:
                            raise HandlerError(u"Can't read VPN key '%s' (%s)'"
                                                % (e.filename, e.strerror))

                        v.pub_key = pub
                        v.priv_key = priv
                    except ExecutionError, e:
                        log.debug(u'VpnHandler._write_config: error executing '
                                    'the command: %r', e)

                vars = dict(
                    vpn = v,
                )
                self._write_single_config('tinc.conf',
                                path.join(v.vpn_src, 'tinc.conf'), vars)
                self._write_single_config('tinc-up',
                                path.join(v.vpn_src, 'tinc-up'), vars)
                for h in v.hosts.values():
                    if not h._delete:
                        vars = dict(
                            host = h,
                        )
                        self._write_single_config('host',
                                path.join(v.vpn_src, 'hosts', h.name), vars)
                    else:
                        log.debug(u'VpnHandler._write_config: removing...')
                        try:
                            # FIXME use os.unlink()
                            call(('rm','-f',
                                    path.join(v.vpn_src, 'hosts', h.name)))
                            del v.hosts[h.name]
                        except ExecutionError, e:
                            log.debug(u'VpnHandler._write_config: error '
                                    'removing files: %r', e)
            else:
                #delete the vpn root at tinc dir
                if path.exists('/etc/tinc/' + v.vpn_src):
                    self.stop(v.vpn_src)
                    call(('rm','-rf','/etc/tinc/' + v.vpn_src))
                    del self.vpns[v.vpn_src]


if __name__ == '__main__':

    logging.basicConfig(
        level   = logging.DEBUG,
        format  = '%(asctime)s %(levelname)-8s %(message)s',
        datefmt = '%H:%M:%S',
    )

    v = VpnHandler()
    v.add('prueba','sarasa','192.168.0.188','255.255.255.0')
    v.host.add('prueba', 'azazel' ,'192.168.0.77', '192.168.0.0',
                'kjdhfkbdskljvkjblkbjeslkjbvkljbselvslberjhbvslbevlhb')
    v.commit()


# vim: set encoding=utf-8 et sw=4 sts=4 :

import os
from os import path

from pymin.seqtools import Sequence
from pymin.dispatcher import Handler, handler, HandlerError
from pymin.services.util import Restorable, ConfigWriter, InitdHandler, \
                                TransactionalHandler, DictSubHandler, DictComposedSubHandler, call, ExecutionError


class Host(Sequence):
    def __init__(self, vpn_src, ip, vpn_src_net, key):
        self.name = vpn_src
        self.ip = ip
        self.src_net = vpn_src_net
        self.pub_key = key
        self.dele = False

    def as_tuple(self):
        return(self.name, self.ip, self.src_net, self.pub_key)

class HostHandler(DictComposedSubHandler):

    handler_help = u"Manage hosts for a vpn"
    _comp_subhandler_cont = 'vpns'
    _comp_subhandler_attr = 'hosts'
    _comp_subhandler_class = Host

    @handler('usage: add <vpn_src> <ip> <vpn_src_net> <key>')
    def delete(self, vpn_src, host):
        DictComposedSubHandler.delete(self, vpn_src, host)
        if vpn_src in parent.vpns:
            if host in parent.vpns[vpn_src].hosts:
                parent.vpns[vpn_src].hosts[host].dele = True


class Vpn(Sequence):
    def __init__(self, vpn_src, vpn_dst, vpn_src_ip, vpn_src_mask, pub_key, priv_key):
        self.vpn_src = vpn_src
        self.vpn_dst = vpn_dst
        self.vpn_src_ip = vpn_src_ip
        self.vpn_src_mask = vpn_src_mask
        self.pub_key = pub_key
        self.priv_key = priv_key
        self.hosts = dict()
        self.dele = False

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
        DictSubHandler.__init__(self,self)
        self._config_writer_cfg_dir = config_dir
        self._persistent_dir = pickle_dir
        self._config_build_templates()
        self._restore()
        self.host = HostHandler(self)

    @handler('usage : add <vpn_name> <vpn_dst> <vpn_src_ip> <vpn_src_mask>')
    def add(self, vpn_src, vpn_dst, vpn_src_ip, vpn_src_mask):
        if not vpn_src in self.vpns:
            DictSubHandler.add(self,  vpn_src, vpn_dst, vpn_src_ip, vpn_src_mask, None, None)
        elif vpn_src in self.vpns:
            if self.vpns[vpn_src].dele :
                self.vpns[vpn_src] = False

    @handler('usage : delete <vpn_name>')
    def delete(self, vpn_src):
        if vpn_src in self.vpns:
            self.vpns[vpn_src].dele = True;


    @handler('usage: start <vpn_name>')
    def start(self, vpn_src):
        if vpn_src in self.vpns:
            call(('tincd','--net=',vpn_src))

    @handler('usage: stop <vpn_name>')
    def stop(self, vpn_src):
        if vpn_src in self.vpns:
            if path.exists('/var/lib/run/tincd.' + vpn_src + '.pid'):
                pid = file('/var/lib/run/tincd.' + vpn_src + '.pid').readline()
                try:
                    os.kill(int(pid.strip()), SIGTERM)
                except OSError:
                    pass # XXX report error?

    def _write_config(self):
        for v in self.vpns.values():
            #chek whether it's been created or not.
            if not v.dele:
                if v.pub_key is None :
                    try:
                        print 'douugh'
                        #first create the directory for the vpn
                        call(('mkdir','-p', path.join(self._config_writer_cfg_dir, v.vpn_src ,'hosts')))
                        #this command should generate 2 files inside the vpn
                        #dir, one rsa_key.priv and one rsa_key.pub
                        #for some reason debian does not work like this
                        call(('tincd','-n', v.vpn_src,'-K','<','/dev/null'))
                        #open the created files and load the keys
                        f = file(path.join(self._config_writer_cfg_dir, v.vpn_src , 'rsa_key.priv'), 'r')
                        priv = f.read()
                        f.close()
                        f = file(path.join(self._config_writer_cfg_dir, v.vpn_src ,'rsa_key.pub'), 'r')
                        pub = f.read()
                        f.close()
                        v.pub_key = pub
                        v.priv_key = priv
                    except ExecutionError, e:
                        print e

                vars = dict(
                    vpn = v,
                )
                self._write_single_config('tinc.conf',path.join(v.vpn_src,'tinc.conf'),vars)
                self._write_single_config('tinc-up',path.join(v.vpn_src,'tinc-up'),vars)
                for h in v.hosts.values():
                    if not h.dele:
                        vars = dict(
                            host = h,
                        )
                        self._write_single_config('host',path.join(v.vpn_src,'hosts',h.name),vars)
                    else:
                        try:
                            call(('rm','-f', path.join(v.vpn_src,'hosts',h.name)))
                            del v.hosts[h.name]
                        except ExecutionError, e:
                            print e
            else:
                #delete the vpn root at tinc dir
                if path.exists('/etc/tinc/' + v.vpn_src):
                    self.stop(v.vpn_src)
                    call(('rm','-rf','/etc/tinc/' + v.vpn_src))
                    del self.vpns[v.vpn_src]


if __name__ == '__main__':
    v = VpnHandler()
    v.add('test','127.0.0.1','192.168.0.1','255.255.255.0')
    #v.host.add('test', 'sarasa' ,'127.0.0.1', '205.25.36.36','kjdhfkbdskljvkjblkbjeslkjbvkljbselvslberjhbvslbevlhb')
    v.delete('test')
    v.commit()

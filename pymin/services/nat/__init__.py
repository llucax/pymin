# vim: set encoding=utf-8 et sw=4 sts=4 :

from os import path
import logging ; log = logging.getLogger('pymin.services.nat')

from pymin.seqtools import Sequence
from pymin.dispatcher import Handler, handler, HandlerError
from pymin.services.util import Restorable, ConfigWriter, RestartHandler, \
                                ReloadHandler, TransactionalHandler, \
                                ServiceHandler, ListSubHandler, call

__all__ = ('NatHandler',)

class PortForward(Sequence):
    r"""PortForward(dev, protocol, port, dst[, dst_port[, ...]]) -> PortForward.

    dev - Netword device to use.
    protocol - TCP or UDP.
    port - Port to forward.
    dst - Destination IP address.
    dst_port - Destination port (at dst).
    src_net - Source network to apply the forward (as IP/mask).
    dst_net - Source network to apply the forward (as IP/mask).
    """

    def __init__(self, dev, protocol, port, dst, dst_port=None, src_net=None,
                       dst_net=None):
        r"Initialize object, see class documentation for details."
        # TODO Validate
        self.dev = dev
        self.protocol = protocol
        self.port = port
        self.dst = dst
        self.dst_port = dst_port
        self.src_net = src_net
        self.dst_net = dst_net

    def update(self, dev=None, protocol=None, port=None, dst=None,
                    dst_port=None, src_net=None, dst_net=None):
        r"update([dev[, ...]]) -> Update the values of a port (see class doc)."
        # TODO Validate
        if dev is not None: self.dev = dev
        if protocol is not None: self.protocol = protocol
        if port is not None: self.port = port
        if dst is not None: self.dst = dst
        if dst_port is not None: self.dst_port = dst_port
        if src_net is not None: self.src_net = src_net
        if dst_net is not None: self.dst_net = dst_net

    def as_tuple(self):
        r"Return a tuple representing the port forward."
        return (self.dev, self.protocol, self.port, self.dst, self.dst_port,
                    self.src_net, self.dst_net)

    def as_call_list(self, index=None):
        if self.dst_port is not None:
            self.dst = self.dst + ':' + self.dst_port
        cmd = ['-t', 'nat', '-I', 'PREROUTING']
        if index is not None:
            cmd.append(str(index))
        cmd.extend(('-i', self.dev, '-j', 'DNAT', '--to', self.dst,
                '-p', self.protocol, '--dport', self.port))
        if self.src_net is not None:
            cmd.extend(('-s', self.src_net))
        if self.dst_net is not None:
            cmd.extend(('-d', self.dst_net))
        return cmd

class PortForwardHandler(ListSubHandler):
    r"""PortForwardHandler(parent) -> PortForwardHandler instance.

    This class is a helper for NatHandler to do all the work related to port
    forwarding.

    parent - The parent service handler.
    """

    handler_help = u"Manage NAT port forwarding."

    _cont_subhandler_attr = 'ports'
    _cont_subhandler_class = PortForward

class SNat(Sequence):
    r"""SNat(dev, src[, src_net]) -> SNat instance.

    dev - Netword device to use.
    src - Source IP address.
    src_net - Source network to apply the NAT (as IP/mask).
    """

    def __init__(self, dev, src, src_net=None):
        r"Initialize object, see class documentation for details."
        # TODO Validate
        self.dev = dev
        self.src = src
        self.src_net = src_net

    def update(self, dev=None, src=None, src_net=None):
        r"update([dev[, ...]]) -> Update the values of a snat (see class doc)."
        # TODO Validate
        if dev is not None: self.dev = dev
        if src is not None: self.src = src
        if src_net is not None: self.src_net = src_net

    def __cmp__(self, other):
        r"Compares two SNat objects."
        return cmp(self.as_tuple(), other.as_tuple())

    def as_tuple(self):
        r"Return a tuple representing the snat."
        return (self.dev, self.src, self.src_net)

    def as_call_list(self, index=None):
        cmd = ['-t', 'nat', '-I', 'POSTROUTING']
        if index is not None:
            cmd.append(str(index))
        cmd.extend(('-o', self.dev, '-j', 'SNAT', '--to', self.src))
        if self.src_net is not None:
            cmd.extend(('-s', self.src_net))
        return cmd

class SNatHandler(ListSubHandler):
    r"""SNatHandler(parent) -> SNatHandler instance.

    This class is a helper for NatHandler to do all the work related to
    Source NAT.

    parent - The parent service handler.
    """

    handler_help = u"Manage source NAT."

    _cont_subhandler_attr = 'snats'
    _cont_subhandler_class = SNat

class Masq(Sequence):
    r"""Masq(dev, src_net) -> Masq instance.

    dev - Netword device to use.
    src_net - Source network to apply the masquerade (as IP/mask).
    """

    def __init__(self, dev, src_net):
        r"Initialize object, see class documentation for details."
        # TODO Validate
        self.dev = dev
        self.src_net = src_net

    def update(self, dev=None, src_net=None):
        r"update([dev[, ...]]) -> Update the values of a masq (see class doc)."
        # TODO Validate
        if dev is not None: self.dev = dev
        if src_net is not None: self.src_net = src_net

    def __cmp__(self, other):
        r"Compares two Masq objects."
        return cmp(self.as_tuple(), other.as_tuple())

    def as_tuple(self):
        r"Return a tuple representing the masquerade."
        return (self.dev, self.src_net)

    def as_call_list(self, index=None):
        cmd = ['-t', 'nat', '-I', 'POSTROUTING']
        if index is not None:
            cmd.append(str(index))
        cmd.extend(('-o', self.dev, '-j', 'MASQUERADE', '-s', self.src_net))
        return cmd

class MasqHandler(ListSubHandler):
    r"""MasqHandler(parent) -> MasqHandler instance.

    This class is a helper for NatHandler to do all the work related to
    masquerading.

    parent - The parent service handler.
    """

    handler_help = u"Manage NAT masquerading."

    _cont_subhandler_attr = 'masqs'
    _cont_subhandler_class = Masq

class NatHandler(Restorable, ConfigWriter, ReloadHandler, ServiceHandler,
                        TransactionalHandler):
    r"""NatHandler([pickle_dir[, config_dir]]) -> NatHandler instance.

    Handles NAT commands using iptables.

    pickle_dir - Directory where to write the persistent configuration data.

    config_dir - Directory where to store de generated configuration files.

    Both defaults to the current working directory.
    """

    handler_help = u"Manage NAT (Network Address Translation) service."

    _persistent_attrs = ('ports', 'snats', 'masqs')

    _restorable_defaults = dict(
        ports=list(),
        snats=list(),
        masqs=list(),
    )

    def _service_start(self):
        log.debug(u'NatHandler._service_start(): flushing nat table')
        call(('iptables', '-t', 'nat', '-F'))
        for (index, port) in enumerate(self.ports):
            log.debug(u'NatHandler._service_start: adding port %r', port)
            call(['iptables'] + port.as_call_list(index+1))
        for (index, snat) in enumerate(self.snats):
            log.debug(u'NatHandler._service_start: adding snat %r', snat)
            call(['iptables'] + snat.as_call_list(index+1))
        for (index, masq) in enumerate(self.masqs):
            log.debug(u'NatHandler._service_start: adding masq %r', masq)
            call(['iptables'] + masq.as_call_list(index+1))

    def _service_stop(self):
        log.debug(u'NatHandler._service_stop(): flushing nat table')
        call(('iptables', '-t', 'nat', '-F'))

    _service_restart = _service_start

    def __init__(self, pickle_dir='.'):
        r"Initialize the object, see class documentation for details."
        log.debug(u'NatHandler(%r)', pickle_dir)
        self._persistent_dir = pickle_dir
        ServiceHandler.__init__(self)
        self.forward = PortForwardHandler(self)
        self.snat = SNatHandler(self)
        self.masq = MasqHandler(self)


if __name__ == '__main__':

    logging.basicConfig(
        level   = logging.DEBUG,
        format  = '%(asctime)s %(levelname)-8s %(message)s',
        datefmt = '%H:%M:%S',
    )

    import os

    handler = NatHandler()

    def dump():
        print '-' * 80
        print 'Forwarded ports:'
        print handler.forward.show()
        print '-' * 10
        print 'SNat:'
        print handler.snat.show()
        print '-' * 10
        print 'Masq:'
        print handler.masq.show()
        print '-' * 80

    dump()
    handler.forward.add('eth0','tcp','80', '192.168.0.9', '8080')
    handler.forward.update(0, dst_net='192.168.0.188/32')
    handler.forward.add('eth0', 'udp', '53', '192.168.1.0')
    handler.commit()
    handler.stop()
    dump()
    handler.snat.add('eth0', '192.168.0.9')
    handler.snat.update(0, src_net='192.168.0.188/32')
    handler.snat.add('eth0', '192.168.1.0')
    handler.commit()
    dump()
    dump()
    handler.masq.add('eth0', '192.168.0.9/24')
    handler.masq.update(0, src_net='192.168.0.188/30')
    handler.masq.add('eth1', '192.168.1.0/24')
    handler.commit()
    dump()

    os.system('rm -f *.pkl')


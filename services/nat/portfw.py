# vim: set encoding=utf-8 et sw=4 sts=4 :

from pymin.seqtools import Sequence
from pymin.service.util import ListSubHandler

__all__ = ('PortForwardHandler',)


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


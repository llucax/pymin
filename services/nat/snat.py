# vim: set encoding=utf-8 et sw=4 sts=4 :

from pymin.seqtools import Sequence
from pymin.service.util import ListSubHandler

__all__ = ('SNatHandler',)


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


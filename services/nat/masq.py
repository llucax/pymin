# vim: set encoding=utf-8 et sw=4 sts=4 :

from pymin.seqtools import Sequence
from pymin.service.util import ListSubHandler

__all__ = ('MasqHandler',)


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


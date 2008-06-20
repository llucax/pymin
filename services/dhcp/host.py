# vim: set encoding=utf-8 et sw=4 sts=4 :

from os import path
import logging ; log = logging.getLogger('pymin.services.dhcp')

from pymin.seqtools import Sequence
from pymin.service.util import DictSubHandler

__all__ = ('HostHandler',)


class Host(Sequence):
    r"""Host(name, ip, mac) -> Host instance :: Class representing a host.

    name - Host name, should be a fully qualified name, but no checks are done.
    ip - IP assigned to the hostname.
    mac - MAC address to associate to the hostname.
    """

    def __init__(self, name, ip, mac):
        r"Initialize Host object, see class documentation for details."
        self.name = name
        self.ip = ip
        self.mac = mac

    def as_tuple(self):
        r"Return a tuple representing the host."
        return (self.name, self.ip, self.mac)

    def update(self, ip=None, mac=None):
        if ip is not None:
            self.ip = ip
        if mac is not None:
            self.mac = mac

class HostHandler(DictSubHandler):
    r"""HostHandler(parent) -> HostHandler instance :: Handle a list of hosts.

    This class is a helper for DhcpHandler to do all the work related to hosts
    administration.
    """

    handler_help = u"Manage DHCP hosts"

    _cont_subhandler_attr = 'hosts'
    _cont_subhandler_class = Host


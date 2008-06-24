# vim: set encoding=utf-8 et sw=4 sts=4 :

from os import path
import logging ; log = logging.getLogger('pymin.services.dhcp')

from pymin.validation import Item, Field, Any, IPAddress, MACAddress, \
                             HostName, FullyQualifiedHostName
from pymin.service.util import DictSubHandler

__all__ = ('HostHandler',)


class Host(Item):
    r"""Host(name, ip, mac) -> Host instance :: Class representing a host.

    name - Host name, should be a fully qualified name, but no checks are done.
    ip - IP assigned to the hostname.
    mac - MAC address to associate to the hostname.
    """
    name = Field(Any(HostName(not_empty=True),
                     FullyQualifiedHostName(not_empty=True)))
    ip = Field(IPAddress(not_empty=True))
    mac = Field(MACAddress(add_colons=True, not_empty=True))

class HostHandler(DictSubHandler):
    r"""HostHandler(parent) -> HostHandler instance :: Handle a list of hosts.

    This class is a helper for DhcpHandler to do all the work related to hosts
    administration.
    """

    handler_help = u"Manage DHCP hosts"

    _cont_subhandler_attr = 'hosts'
    _cont_subhandler_class = Host


# vim: set encoding=utf-8 et sw=4 sts=4 :

from os import path

from pymin.seqtools import Sequence
from pymin.dispatcher import Handler, handler, HandlerError
from pymin.services.util import Restorable, ConfigWriter, InitdHandler, \
                                TransactionalHandler, ParametersHandler

__ALL__ = ('DhcpHandler', 'Error', 'HostError', 'HostAlreadyExistsError',
            'HostNotFoundError')

class Error(HandlerError):
    r"""
    Error(message) -> Error instance :: Base DhcpHandler exception class.

    All exceptions raised by the DhcpHandler inherits from this one, so you can
    easily catch any DhcpHandler exception.

    message - A descriptive error message.
    """

    def __init__(self, message):
        r"Initialize the Error object. See class documentation for more info."
        self.message = message

    def __str__(self):
        return self.message

class HostError(Error, KeyError):
    r"""
    HostError(hostname) -> HostError instance

    This is the base exception for all host related errors.
    """

    def __init__(self, hostname):
        r"Initialize the object. See class documentation for more info."
        self.message = 'Host error: "%s"' % hostname

class HostAlreadyExistsError(HostError):
    r"""
    HostAlreadyExistsError(hostname) -> HostAlreadyExistsError instance

    This exception is raised when trying to add a hostname that already exists.
    """

    def __init__(self, hostname):
        r"Initialize the object. See class documentation for more info."
        self.message = 'Host already exists: "%s"' % hostname

class HostNotFoundError(HostError):
    r"""
    HostNotFoundError(hostname) -> HostNotFoundError instance

    This exception is raised when trying to operate on a hostname that doesn't
    exists.
    """

    def __init__(self, hostname):
        r"Initialize the object. See class documentation for more info."
        self.message = 'Host not found: "%s"' % hostname


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

class HostHandler(Handler):
    r"""HostHandler(hosts) -> HostHandler instance :: Handle a list of hosts.

    This class is a helper for DhcpHandler to do all the work related to hosts
    administration.

    hosts - A dictionary with string keys (hostnames) and Host instances values.
    """

    def __init__(self, hosts):
        r"Initialize HostHandler object, see class documentation for details."
        self.hosts = hosts

    @handler(u'Add a new host.')
    def add(self, name, ip, mac):
        r"add(name, ip, mac) -> None :: Add a host to the hosts list."
        if name in self.hosts:
            raise HostAlreadyExistsError(name)
        self.hosts[name] = Host(name, ip, mac)

    @handler(u'Update a host.')
    def update(self, name, ip=None, mac=None):
        r"update(name[, ip[, mac]]) -> None :: Update a host of the hosts list."
        if not name in self.hosts:
            raise HostNotFoundError(name)
        if ip is not None:
            self.hosts[name].ip = ip
        if mac is not None:
            self.hosts[name].mac = mac

    @handler(u'Delete a host.')
    def delete(self, name):
        r"delete(name) -> None :: Delete a host of the hosts list."
        if not name in self.hosts:
            raise HostNotFoundError(name)
        del self.hosts[name]

    @handler(u'Get information about a host.')
    def get(self, name):
        r"get(name) -> Host :: List all the information of a host."
        if not name in self.hosts:
            raise HostNotFoundError(name)
        return self.hosts[name]

    @handler(u'List hosts.')
    def list(self):
        r"list() -> tuple :: List all the hostnames."
        return self.hosts.keys()

    @handler(u'Get information about all hosts.')
    def show(self):
        r"show() -> list of Hosts :: List all the complete hosts information."
        return self.hosts.values()


class DhcpHandler(Restorable, ConfigWriter, InitdHandler, TransactionalHandler,
                  ParametersHandler):
    r"""DhcpHandler([pickle_dir[, config_dir]]) -> DhcpHandler instance.

    Handles DHCP service commands for the dhcpd program.

    pickle_dir - Directory where to write the persistent configuration data.

    config_dir - Directory where to store de generated configuration files.

    Both defaults to the current working directory.
    """

    _initd_name = 'dhcpd'

    _persistent_attrs = ('params', 'hosts')

    _restorable_defaults = dict(
            hosts = dict(),
            params  = dict(
                domain_name = 'example.com',
                dns_1       = 'ns1.example.com',
                dns_2       = 'ns2.example.com',
                net_address = '192.168.0.0',
                net_mask    = '255.255.255.0',
                net_start   = '192.168.0.100',
                net_end     = '192.168.0.200',
                net_gateway = '192.168.0.1',
            ),
    )

    _config_writer_files = 'dhcpd.conf'
    _config_writer_tpl_dir = path.join(path.dirname(__file__), 'templates')

    def __init__(self, pickle_dir='.', config_dir='.'):
        r"Initialize DhcpHandler object, see class documentation for details."
        self._persistent_dir = pickle_dir
        self._config_writer_cfg_dir = config_dir
        self._config_build_templates()
        self._restore()
        self.host = HostHandler(self.hosts)

    def _get_config_vars(self, config_file):
        return dict(hosts=self.hosts.values(), **self.params)


if __name__ == '__main__':

    import os

    h = DhcpHandler()

    def dump():
        print '-' * 80
        print 'Variables:', h.list()
        print h.show()
        print
        print 'Hosts:', h.host.list()
        print h.host.show()
        print '-' * 80

    dump()

    h.host.add('my_name','192.168.0.102','00:12:ff:56')

    h.host.update('my_name','192.168.0.192','00:12:ff:56')

    h.host.add('nico','192.168.0.188','00:00:00:00')

    h.set('domain_name','baryon.com.ar')

    try:
        h.set('sarasa','baryon.com.ar')
    except KeyError, e:
        print 'Error:', e

    h.commit()

    dump()

    os.system('rm -f *.pkl ' + ' '.join(h._config_writer_files))


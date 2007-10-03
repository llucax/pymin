# vim: set encoding=utf-8 et sw=4 sts=4 :

from os import path

from seqtools import Sequence
from dispatcher import Handler, handler, HandlerError
from services.util import Restorable, ConfigWriter
from services.util import InitdHandler, TransactionalHandler

__ALL__ = ('ProxyHandler', 'Error', 'HostError', 'HostAlreadyExistsError',
            'HostNotFoundError', 'ParameterError', 'ParameterNotFoundError')

class Error(HandlerError):
    r"""
    Error(command) -> Error instance :: Base DnsHandler exception class.

    All exceptions raised by the DnsHandler inherits from this one, so you can
    easily catch any DnsHandler exception.

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

class ParameterError(Error, KeyError):
    r"""
    ParameterError(paramname) -> ParameterError instance

    This is the base exception for all DhcpHandler parameters related errors.
    """

    def __init__(self, paramname):
        r"Initialize the object. See class documentation for more info."
        self.message = 'Parameter error: "%s"' % paramname

class ParameterNotFoundError(ParameterError):
    r"""
    ParameterNotFoundError(hostname) -> ParameterNotFoundError instance

    This exception is raised when trying to operate on a parameter that doesn't
    exists.
    """

    def __init__(self, paramname):
        r"Initialize the object. See class documentation for more info."
        self.message = 'Parameter not found: "%s"' % paramname

class Host(Sequence):

    def __init__(self,ip):
        self.ip = ip

    def as_tuple(self):
        return (self.ip)

class HostHandler(Handler):

    def __init__(self, hosts):
        self.hosts = hosts

    @handler(u'Adds a host')
    def add(self, ip):
        if ip in self.hosts:
            raise HostAlreadyExistsError(ip)
        self.hosts[ip] = Host(ip)

    @handler(u'Deletes a host')
    def delete(self, ip):
        if not ip in self.hosts:
            raise HostNotFoundError(ip)
        del self.hosts[ip]

    @handler(u'Shows all hosts')
    def list(self):
        return self.hosts.keys()

    @handler(u'Get information about all hosts')
    def show(self):
        return self.hosts.items()


class ProxyHandler(Restorable, ConfigWriter, InitdHandler,
                                            TransactionalHandler):

    _initd_name = 'squid'

    _persistent_vars = ('vars', 'hosts')

    _restorable_defaults = dict(
            hosts = dict(),
            vars  = dict(
                ip   = '192.168.0.1',
                port = '8080',
            ),
    )

    _config_writer_files = 'squid.conf'
    _config_writer_tpl_dir = path.join(path.dirname(__file__), 'templates')

    def __init__(self, pickle_dir='.', config_dir='.'):
        r"Initialize DhcpHandler object, see class documentation for details."
        self._persistent_dir = pickle_dir
        self._config_writer_cfg_dir = config_dir
        self._config_build_templates()
        self._restore()
        self.host = HostHandler(self.hosts)

    def _get_config_vars(self, config_file):
        return dict(hosts=self.hosts.values(), **self.vars)

    @handler(u'Set a Proxy parameter')
    def set(self, param, value):
        r"set(param, value) -> None :: Set a Proxy parameter."
        if not param in self.vars:
            raise ParameterNotFoundError(param)
        self.vars[param] = value

    @handler(u'Get a DNS parameter')
    def get(self, param):
        r"get(param) -> None :: Get a Proxy parameter."
        if not param in self.vars:
            raise ParameterNotFoundError(param)
        return self.vars[param]

    @handler(u'List Proxy parameters')
    def list(self):
        return self.vars.keys()

    @handler(u'Get all Proxy parameters, with their values.')
    def show(self):
        return self.vars.values()


if __name__ == '__main__':

    px = ProxyHandler()
    px.set('ip','192.66.66.66')
    px.set('port','666')
    px.host.add('192.168.0.25.25')
    px.host.add('192.168.0.25.26')
    px.host.add('192.168.0.25.27')
    px.host.delete('192.168.0.25.27')
    px.commit()
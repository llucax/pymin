# vim: set encoding=utf-8 et sw=4 sts=4 :

from os import path

from pymin.seqtools import Sequence
from pymin.dispatcher import Handler, handler, HandlerError
from pymin.services.util import Restorable, ConfigWriter, InitdHandler, \
                                TransactionalHandler, ParametersHandler

import crypt

__ALL__ = ('ProxyHandler', 'Error', 'HostError', 'HostAlreadyExistsError',
            'HostNotFoundError')

class Error(HandlerError):
    r"""
    Error(command) -> Error instance :: Base DnsHandler exception class.

    All exceptions raised by the DnsHandler inherits from this one, so you can
    easily catch any DnsHandler exception.

    message - A descriptive error message.
    """
    pass

class HostError(Error, KeyError):
    r"""
    HostError(hostname) -> HostError instance

    This is the base exception for all host related errors.
    """

    def __init__(self, hostname):
        r"Initialize the object. See class documentation for more info."
        self.message = u'Host error: "%s"' % hostname

class HostAlreadyExistsError(HostError):
    r"""
    HostAlreadyExistsError(hostname) -> HostAlreadyExistsError instance

    This exception is raised when trying to add a hostname that already exists.
    """

    def __init__(self, hostname):
        r"Initialize the object. See class documentation for more info."
        self.message = u'Host already exists: "%s"' % hostname

class HostNotFoundError(HostError):
    r"""
    HostNotFoundError(hostname) -> HostNotFoundError instance

    This exception is raised when trying to operate on a hostname that doesn't
    exists.
    """

    def __init__(self, hostname):
        r"Initialize the object. See class documentation for more info."
        self.message = u'Host not found: "%s"' % hostname


class Host(Sequence):

    def __init__(self,ip):
        self.ip = ip

    def as_tuple(self):
        return (self.ip)

class HostHandler(Handler):

    handler_help = u"Manage proxy hosts"

    def __init__(self, parent):
        self.parent = parent

    @handler(u'Adds a host')
    def add(self, ip):
        if ip in self.parent.hosts:
            raise HostAlreadyExistsError(ip)
        self.parent.hosts[ip] = Host(ip)

    @handler(u'Deletes a host')
    def delete(self, ip):
        if not ip in self.parent.hosts:
            raise HostNotFoundError(ip)
        del self.parent.hosts[ip]

    @handler(u'Shows all hosts')
    def list(self):
        return self.parent.hosts.keys()

    @handler(u'Get information about all hosts')
    def show(self):
        return self.parent.hosts.items()


class UserHandler(Handler):

    def __init__(self, parent):
        self.parent = parent
	
    @handler('Adds a user')
    def add(self, user, password):
        if user in self.parent.users:
            raise UserAlreadyExistsError(user)
        self.parent.users[user] = crypt.crypt(password,'BA')
    
    @handler('Deletes a user')
    def delete(self, user):
        if not user in self.parent.users:
            raise UserNotFound(user)
        del self.parent.users[user]

class ProxyHandler(Restorable, ConfigWriter, InitdHandler,
                   TransactionalHandler, ParametersHandler):

    handler_help = u"Manage proxy service"

    _initd_name = 'squid'

    _persistent_attrs = ('params', 'hosts', 'users')

    _restorable_defaults = dict(
            hosts = dict(),
            params  = dict(
                ip   = '192.168.0.1',
                port = '8080',
            ),
            users = dict(),
    )

    _config_writer_files = ('squid.conf','users.conf')
    _config_writer_tpl_dir = path.join(path.dirname(__file__), 'templates')

    def __init__(self, pickle_dir='.', config_dir='.'):
        r"Initialize DhcpHandler object, see class documentation for details."
        self._persistent_dir = pickle_dir
        self._config_writer_cfg_dir = config_dir
        self._config_build_templates()
        self._restore()
        self.host = HostHandler(self)
        self.user = UserHandler(self)

    def _get_config_vars(self, config_file):
        if config_file == 'squid.conf':
            return dict(hosts=self.hosts.values(), **self.params)
        return dict(users=self.users)


if __name__ == '__main__':

    px = ProxyHandler()
    px.set('ip','192.66.66.66')
    px.set('port','666')
    px.host.add('192.168.0.25.25')
    px.host.add('192.168.0.25.26')
    px.host.add('192.168.0.25.27')
    px.host.delete('192.168.0.25.27')
    px.user.add('lala','soronga')
    px.user.add('culo','sarasa')
    px.commit()

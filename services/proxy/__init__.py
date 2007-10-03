# vim: set encoding=utf-8 et sw=4 sts=4 :

from mako.template import Template
from mako.runtime import Context
from subprocess import Popen, PIPE
from os import path
try:
    import cPickle as pickle
except ImportError:
    import pickle

try:
    from seqtools import Sequence
except ImportError:
    # NOP for testing
    class Sequence: pass
try:
    from dispatcher import handler, HandlerError, Handler
except ImportError:
    # NOP for testing
    class HandlerError(RuntimeError): pass
    class Handler: pass
    def handler(help):
        def wrapper(f):
            return f
        return wrapper

__ALL__ = ('ProxyHandler')

pickle_ext = '.pkl'
pickle_vars = 'vars'
pickle_hosts= 'hosts'
pickle_users = 'users'
config_filename = 'squid.conf'

template_dir = path.join(path.dirname(__file__), 'templates')


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


class ProxyHandler(Handler):

    def __init__(self, pickle_dir='.', config_dir='.'):
        self.pickle_dir = pickle_dir
        self.config_dir = config_dir
        f = path.join(template_dir, config_filename)
        self.config_template = Template(filename=f)
        try:
            self._load()
        except IOError:
            self.hosts = dict()
            self.vars = dict(
                    ip = '192.168.0.1',
                    port = '8080',
                )
        self.host = HostHandler(self.hosts)

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

    @handler(u'Start the service.')
    def start(self):
        r"start() -> None :: Start the DNS service."
        #esto seria para poner en una interfaz
        #y seria el hook para arrancar el servicio
        pass

    @handler(u'Stop the service.')
    def stop(self):
        r"stop() -> None :: Stop the DNS service."
        #esto seria para poner en una interfaz
        #y seria el hook para arrancar el servicio
        pass

    @handler(u'Restart the service.')
    def restart(self):
        r"restart() -> None :: Restart the DNS service."
        #esto seria para poner en una interfaz
        #y seria el hook para arrancar el servicio
        pass

    @handler(u'Reload the service config (without restarting, if possible)')
    def reload(self):
        r"reload() -> None :: Reload the configuration of the DNS service."
        #esto seria para poner en una interfaz
        #y seria el hook para arrancar el servicio
        print('reloading configuration')

    @handler(u'Commit the changes (reloading the service, if necessary).')
    def commit(self):
        r"commit() -> None :: Commit the changes and reload the DNS service."
        #esto seria para poner en una interfaz
        #y seria que hace el pickle deberia llamarse
        #al hacerse un commit
        self._dump()
        self._write_config()
        self.reload()

    @handler(u'Discard all the uncommited changes.')
    def rollback(self):
        r"rollback() -> None :: Discard the changes not yet commited."
        self._load()

    def _dump(self):
        r"_dump() -> None :: Dump all persistent data to pickle files."
        # XXX podría ir en una clase base
        self._dump_var(self.vars, pickle_vars)
        self._dump_var(self.hosts, pickle_hosts)

    def _load(self):
        r"_load() -> None :: Load all persistent data from pickle files."
        # XXX podría ir en una clase base
        self.vars = self._load_var(pickle_vars)
        self.hosts = self._load_var(pickle_hosts)

    def _pickle_filename(self, name):
        r"_pickle_filename() -> string :: Construct a pickle filename."
        # XXX podría ir en una clase base
        return path.join(self.pickle_dir, name) + pickle_ext

    def _dump_var(self, var, name):
        r"_dump_var() -> None :: Dump a especific variable to a pickle file."
        # XXX podría ir en una clase base
        pkl_file = file(self._pickle_filename(name), 'wb')
        pickle.dump(var, pkl_file, 2)
        pkl_file.close()

    def _load_var(self, name):
        r"_load_var() -> object :: Load a especific pickle file."
        # XXX podría ir en una clase base
        return pickle.load(file(self._pickle_filename(name)))

    def _write_config(self):
        r"_write_config() -> None :: Generate all the configuration files."
        out_file = file(path.join(self.config_dir, config_filename), 'w')
        ctx = Context(out_file,
                    ip = self.vars['ip'],
                    port = self.vars['port'],
                    hosts = self.hosts.values()
                    )
        self.config_template.render_context(ctx)
        out_file.close()


if __name__ == '__main__':

    px = ProxyHandler()
    px.set('ip','192.66.66.66')
    px.set('port','666')
    px.host.add('192.168.0.25.25')
    px.host.add('192.168.0.25.26')
    px.host.add('192.168.0.25.27')
    px.host.delete('192.168.0.25.27')
    px.commit()
# vim: set encoding=utf-8 et sw=4 sts=4 :

from mako.template import Template
from mako.runtime import Context
from os import path
try:
    import cPickle as pickle
except ImportError:
    import pickle

__ALL__ = ('DhcpHandler',)

pickle_ext = '.pkl'
pickle_vars = 'vars'
pickle_hosts = 'hosts'

config_filename = 'dhcpd.conf'

template_dir = path.join(path.dirname(__file__), 'templates')

class Host:
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

class HostHandler:
    r"""HostHandler(hosts) -> HostHandler instance :: Handle a list of hosts.

    This class is a helper for DhcpHandler to do all the work related to hosts
    administration.

    hosts - A dictionary with string keys (hostnames) and Host instances values.
    """

    def __init__(self, hosts):
        r"Initialize HostHandler object, see class documentation for details."
        self.hosts = hosts

    def add(self, name, ip, mac):
        r"add(name, ip, mac) -> None :: Add a host to the hosts list."
        # XXX deberia indexar por hostname o por ip? o por mac? :)
        # o por nada... Puedo tener un nombre con muchas IPs? Una IP con muchos
        # nombres? Una MAC con muchas IP? una MAC con muchos nombre? Etc...
        self.hosts[name] = Host(name, ip, mac)

    def update(self, name, ip=None, mac=None):
        r"update(name[, ip[, mac]]) -> None :: Update a host of the hosts list."
        if not name in self.hosts:
            raise KeyError('Host not found')
        if ip is not None:
            self.hosts[name].ip = ip
        if mac is not None:
            self.hosts[name].mac = mac

    def delete(self, name):
        r"delete(name) -> None :: Delete a host of the hosts list."
        if not name in self.hosts:
            raise KeyError('Host not found')
        del self.hosts[name]

    def list(self):
        r"""list() -> CSV string :: List all the hostnames.

        The list is returned as a single CSV line with all the hostnames.
        """
        return ','.join(self.hosts)

    def show(self):
        r"""show() -> CSV string :: List all the complete hosts information.

        The hosts are returned as a CSV list with each host in a line, like:
        hostname,ip,mac
        """
        hosts = self.hosts.values()
        return '\n'.join('%s,%s,%s' % (h.name, h.ip, h.mac) for h in hosts)

class DhcpHandler:
    r"""DhcpHandler([pickle_dir[, config_dir]]) -> DhcpHandler instance.

    Handles DHCP service commands for the dhcpd program.

    pickle_dir - Directory where to write the persistent configuration data.

    config_dir - Directory where to store de generated configuration files.

    Both defaults to the current working directory.
    """

    def __init__(self, pickle_dir='.', config_dir='.'):
        r"Initialize DhcpHandler object, see class documentation for details."
        self.pickle_dir = pickle_dir
        self.config_dir = config_dir
        filename = path.join(template_dir, config_filename)
        self.template = Template(filename=filename)
        try:
            self._load()
        except IOError:
            # This is the first time the handler is used, create a basic
            # setup using some nice defaults
            self.hosts = dict()
            self.vars = dict(
                domain_name = 'example.com',
                dns_1       = 'ns1.example.com',
                dns_2       = 'ns2.example.com',
                net_address = '192.168.0.0',
                net_mask    = '255.255.255.0',
                net_start   = '192.168.0.100',
                net_end     = '192.168.0.200',
                net_gateway = '192.168.0.1',
            )
            self._dump()
            self._write_config()
        self.host = HostHandler(self.hosts)

    def set(self, param, value):
        r"set(param, value) -> None :: Set a DHCP parameter."
        if not param in self.vars:
            raise KeyError('Parameter ' + param + ' not found')
        self.vars[param] = value

    def list(self):
        r"""list() -> CSV string :: List all the parameter names.

        The list is returned as a single CSV line with all the names.
        """
        return ','.join(self.vars)

    def show(self):
        r"""show() -> CSV string :: List all the parameters (with their values).

        The parameters are returned as a CSV list with each parameter in a
        line, like:
        name,value
        """
        return '\n'.join(('%s,%s' % (k, v) for (k, v) in self.vars.items()))

    def start(self):
        r"start() -> None :: Start the DHCP service."
        #esto seria para poner en una interfaz
        #y seria el hook para arrancar el servicio
        pass

    def stop(self):
        r"stop() -> None :: Stop the DHCP service."
        #esto seria para poner en una interfaz
        #y seria el hook para arrancar el servicio
        pass

    def restart(self):
        r"restart() -> None :: Restart the DHCP service."
        #esto seria para poner en una interfaz
        #y seria el hook para arrancar el servicio
        pass

    def reload(self):
        r"reload() -> None :: Reload the configuration of the DHCP service."
        #esto seria para poner en una interfaz
        #y seria el hook para arrancar el servicio
        pass

    def commit(self):
        r"commit() -> None :: Commit the changes and reload the DHCP service."
        #esto seria para poner en una interfaz
        #y seria que hace el pickle deberia llamarse
        #al hacerse un commit
        self._dump()
        self._write_config()
        self.reload()

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
        pickle.dump(var, file(self._pickle_filename(name), 'wb'), 2)

    def _load_var(self, name):
        r"_load_var() -> object :: Load a especific pickle file."
        # XXX podría ir en una clase base
        return pickle.load(file(self._pickle_filename(name)))

    def _write_config(self):
        r"_write_config() -> None :: Generate all the configuration files."
        # XXX podría ir en una clase base, ver como generalizar variables a
        # reemplazar en la template
        out_file = file(path.join(self.config_dir, config_filename), 'w')
        ctx = Context(out_file, hosts=self.hosts.values(), **self.vars)
        self.template.render_context(ctx)

if __name__ == '__main__':

    import os

    dhcp_handler = DhcpHandler()

    def dump():
        print '-' * 80
        print 'Variables:', dhcp_handler.list()
        print dhcp_handler.show()
        print
        print 'Hosts:', dhcp_handler.host.list()
        print dhcp_handler.host.show()
        print '-' * 80

    dump()

    dhcp_handler.host.add('my_name','192.168.0.102','00:12:ff:56')

    dhcp_handler.host.update('my_name','192.168.0.192','00:12:ff:56')

    dhcp_handler.host.add('nico','192.168.0.188','00:00:00:00')

    dhcp_handler.set('domain_name','baryon.com.ar')

    try:
        dhcp_handler.set('sarasa','baryon.com.ar')
    except KeyError, e:
        print 'Error:', e

    dhcp_handler.commit()

    dump()

    for f in (pickle_vars + pickle_ext, pickle_hosts + pickle_ext,
                                                            config_filename):
        os.unlink(f)


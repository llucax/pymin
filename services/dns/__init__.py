# vim: set encoding=utf-8 et sw=4 sts=4 :

from mako.template import Template
from mako.runtime import Context
from os import path
from os import unlink

try:
    import cPickle as pickle
except ImportError:
    import pickle
try:
    from dispatcher import handler
except ImportError:
    def handler(f): return f # NOP for testing

__ALL__ = ('DnsHandler',)

pickle_ext = '.pkl'

pickle_vars = 'vars'
pickle_zones = 'zones'

config_filename = 'named.conf'
zone_filename = 'zoneX.zone'
zone_filename_ext = '.zone'

template_dir = path.join(path.dirname(__file__), 'templates')


class Error(RuntimeError):
    r"""
    Error(command) -> Error instance :: Base DhcpHandler exception class.

    All exceptions raised by the DhcpHandler inherits from this one, so you can
    easily catch any DhcpHandler exception.

    message - A descriptive error message.
    """

    def __init__(self, message):
        r"Initialize the Error object. See class documentation for more info."
        self.message = message

    def __str__(self):
        return self.message

class ZoneError(Error, KeyError):
    r"""
    ZoneError(hostname) -> ZoneError instance

    This is the base exception for all zone related errors.
    """

    def __init__(self, zonename):
        r"Initialize the object. See class documentation for more info."
        self.message = 'Zone error: "%s"' % zonename


class ZoneNotFoundError(ZoneError):
    r"""
    ZoneNotFoundError(zonename) -> ZoneNotFoundError instance

    This exception is raised when trying to operate on a zonename that doesn't
    exists.
    """

    def __init__(self, hostname):
        r"Initialize the object. See class documentation for more info."
        self.message = 'zone not found: "%s"' % hostname


class ZoneAlreadyExistsError(ZoneError):
    r"""
    ZoneAlreadyExistsError(hostname) -> ZoneAlreadyExistsError instance

    This exception is raised when trying to add a zonename that already exists.
    """

    def __init__(self, zonename):
        r"Initialize the object. See class documentation for more info."
        self.message = 'Zone already exists: "%s"' % zonename


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


class MailExchangeError(Error, KeyError):
    r"""
    HostError(hostname) -> HostError instance

    This is the base exception for all host related errors.
    """

    def __init__(self, mx):
        r"Initialize the object. See class documentation for more info."
        self.message = 'Mail Exchange error: "%s"' % mx

class MailExchangeAlreadyExistsError(MailExchangeError):
    r"""
    HostAlreadyExistsError(hostname) -> HostAlreadyExistsError instance

    This exception is raised when trying to add a hostname that already exists.
    """

    def __init__(self, mx):
        r"Initialize the object. See class documentation for more info."
        self.message = 'Mail Exchange already exists: "%s"' % mx

class MailExchangeNotFoundError(MailExchangeError):
    r"""
    HostNotFoundError(hostname) -> HostNotFoundError instance

    This exception is raised when trying to operate on a hostname that doesn't
    exists.
    """

    def __init__(self, mx):
        r"Initialize the object. See class documentation for more info."
        self.message = 'Mail Exchange not found: "%s"' % mx



class NameServerError(Error, KeyError):
    r"""
    HostError(hostname) -> HostError instance

    This is the base exception for all host related errors.
    """

    def __init__(self, ns):
        r"Initialize the object. See class documentation for more info."
        self.message = 'Name Server error: "%s"' % ns

class NameServerAlreadyExistsError(NameServerError):
    r"""
    HostAlreadyExistsError(hostname) -> HostAlreadyExistsError instance

    This exception is raised when trying to add a hostname that already exists.
    """

    def __init__(self, ns):
        r"Initialize the object. See class documentation for more info."
        self.message = 'Mail Exchange already exists: "%s"' % ns

class NameServerNotFoundError(NameServerError):
    r"""
    HostNotFoundError(hostname) -> HostNotFoundError instance

    This exception is raised when trying to operate on a hostname that doesn't
    exists.
    """

    def __init__(self, ns):
        r"Initialize the object. See class documentation for more info."
        self.message = 'Mail Exchange not found: "%s"' % ns


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

class Host:
    def __init__(self, name, ip):
        self.name = name
        self.ip = ip

class HostHandler:
    def __init__(self,zones):
        self.zones = zones

    @handler
    def add(self, name, hostname, ip):
        if not name in self.zones:
            raise ZoneNotFoundError(name)
        if hostname in self.zones[name].hosts:
            raise HostAlreadyExistsError(hostname)
        self.zones[name].hosts[hostname] = Host(hostname, ip)
        self.zones[name].mod = True

    @handler
    def update(self, name, hostname, ip):
        if not name in self.zones:
            raise ZoneNotFoundError(name)
        if not hostname in self.zones[name].hosts:
             raise HostNotFoundError(name)
        self.zones[name].hosts[hostname].ip = ip
        self.zones[name].mod = True

    @handler
    def delete(self, name, hostname):
        r"delete(name) -> None :: Delete a zone from the zone list."
        if not name in self.zones:
            raise ZoneNotFoundError(name)
        if not hostname in self.zones[name].hosts:
             raise HostNotFoundError(name)
        del self.zones[name].hosts[hostname]
        self.zones[name].mod = True

    @handler
    def list(self):
        r"""list() -> CSV string :: List all the hostnames.

        The list is returned as a single CSV line with all the hostnames.
        """
        #return ','.join(self.zones)

    @handler
    def show(self):
        r"""show() -> CSV string :: List all the complete hosts information.

        The hosts are returned as a CSV list with each host in a line, like:
        hostname,ip,mac
        """
        output = ''
        for z in self.zones.values():
            for h in z.hosts.values():
                output += z.name + ',' + h.name + ',' + h.ip + '\n'
        return output


class MailExchange:

    def __init__(self, mx, prio):
        self.mx = mx
        self.prio = prio

class MailExchangeHandler:

    def __init__(self, zones):
        self.zones = zones

    @handler
    def add(self, zonename, mx, prio):
        if not zonename in self.zones:
            raise ZoneNotFoundError(zonename)
        if mx in self.zones[zonename].mxs:
            raise MailExchangeAlreadyExistsError(mx)
        self.zones[zonename].mxs[mx] = MailExchange(mx, prio)
        self.zones[zonename].mod = True

    @handler
    def update(self, zonename, mx, prio):
        if not zonename in self.zones:
            raise ZoneNotFoundError(zonename)
        if not mx in self.zones[zonename].mxs:
            raise MailExchangeNotFoundError(mx)
        self.zones[zonename].mxs[mx].prio = prio
        self.zones[zonename].mod = True

    @handler
    def delete(self, zonename, mx):
        if not zonename in self.zones:
            raise ZoneNotFoundError(zonename)
        if not mx in self.zones[zonename].mxs:
            raise MailExchangeNotFoundError(mx)
        del self.zones[zonename].mxs[mx]
        self.zones[zonename].mod = True

    @handler
    def list(self):
        r"""list() -> CSV string :: List all the hostnames.

        The list is returned as a single CSV line with all the hostnames.
        """
        return ','.join(self.zones)

    @handler
    def show(self):
        r"""show() -> CSV string :: List all the complete hosts information.

        The hosts are returned as a CSV list with each host in a line, like:
        hostname,ip,mac
        """
        zones = self.zones.values()
        return '\n'.join('%s,%s,%s' % (z.name, z.ns1, z.ns2) for z in zones)


class NameServer:

    def __init__(self, name):
        self.name = name


class NameServerHandler:

    def __init__(self, zones):
        self.zones = zones

    def add(self, zone, ns):
        if not zone in self.zones:
            raise ZoneNotFoundError(zone)
        if ns in self.zones[zone].nss:
            raise NameServerAlreadyExistsError(ns)
        self.zones[zone].nss[ns] = NameServer(ns)
        self.zones[zone].mod = True

    def delete(self, zone, ns):
        if not zone in self.zones:
            raise ZoneNotFoundError(zone)
        if not ns in self.zones[zone].nss:
            raise NameServerNotFoundError(ns)
        del self.zones[zone].nss[ns]
        self.zones[zone].mod = True

class Zone:
    def __init__(self, name, ns1, ns2):
        self.name = name
        self.ns1 = ns1
        self.ns2 = ns2
        self.hosts = dict()
        self.mxs = dict()
        self.nss = dict()
        self.mod = False
        self.dele = False

class ZoneHandler:

    r"""ZoneHandler(zones) -> ZoneHandler instance :: Handle a list of zones.

    This class is a helper for DnsHandler to do all the work related to zone
    administration.

    zones - A dictionary with string keys (zone name) and Zone instances values.
    """
    def __init__(self, zones):
        self.zones = zones

    @handler
    def add(self, name, ns1, ns2=None):
        if name in self.zones:
            raise ZoneAlreadyExistsError(name)
        self.zones[name] = Zone(name, ns1, ns2)
        self.zones[name].mod = True

    @handler
    def update(self, name, ns1=None, ns2=None):
        if not name in self.zones:
            raise ZoneNotFoundError(name)
        if self.zones[name].dele:
            raise ZoneNotFoundError(name)
        if ns1 is not None:
            self.zones[name].ns1 = ns1
        if ns2 is not None:
            self.zones[name].ns2 = ns2
        self.zones[name].mod = True

    @handler
    def delete(self, name):
        r"delete(name) -> None :: Delete a zone from the zone list."
        if not name in self.zones:
            raise ZoneNotFoundError(name)
        self.zones[name].dele = True

    @handler
    def list(self):
        r"""list() -> CSV string :: List all the hostnames.

        The list is returned as a single CSV line with all the hostnames.
        """
        return ','.join(self.zones)

    @handler
    def show(self):
        r"""show() -> CSV string :: List all the complete hosts information.

        The hosts are returned as a CSV list with each host in a line, like:
        hostname,ip,mac
        """
        zones = self.zones.values()
        return '\n'.join('%s,%s,%s' % (z.name, z.ns1, z.ns2) for z in zones)

class DnsHandler:
    r"""DnsHandler([pickle_dir[, config_dir]]) -> DnsHandler instance.

    Handles DNS service commands for the dns program.

    pickle_dir - Directory where to write the persistent configuration data.

    config_dir - Directory where to store de generated configuration files.

    Both defaults to the current working directory.
    """

    def __init__(self, pickle_dir='.', config_dir='.'):
        r"Initialize DnsHandler object, see class documentation for details."
        self.pickle_dir = pickle_dir
        self.config_dir = config_dir
        c_filename = path.join(template_dir, config_filename)
        z_filename = path.join(template_dir, zone_filename)
        self.config_template = Template(filename=c_filename)
        self.zone_template = Template(filename=z_filename)
        try :
            self._load()
        except IOError:
            self.zones = dict()
            self.vars = dict(
                isp_dns1 = '',
                isp_dns2 = '',
                bind_addr1 = '',
                bind_addr2 = ''
            )

        self.host = HostHandler(self.zones)
        self.zone = ZoneHandler(self.zones)
        self.mx = MailExchangeHandler(self.zones)
        self.ns = NameServerHandler(self.zones)

    @handler
    def set(self, param, value):
        r"set(param, value) -> None :: Set a DHCP parameter."
        if not param in self.vars:
            raise ParameterNotFoundError(param)
        self.vars[param] = value

    @handler
    def get(self, param):
        r"get(param) -> None :: Get a DHCP parameter."
        if not param in self.vars:
            raise ParameterNotFoundError(param)
        return self.vars[param]

    @handler
    def list(self):
        r"""list() -> CSV string :: List all the parameter names.

        The list is returned as a single CSV line with all the names.
        """
        return ','.join(self.vars)

    @handler
    def show(self):
        r"""show() -> CSV string :: List all the parameters (with their values).

        The parameters are returned as a CSV list with each parameter in a
        line, like:
        name,value
        """
        return '\n'.join(('%s,%s' % (k, v) for (k, v) in self.vars.items()))

    @handler
    def start(self):
        r"start() -> None :: Start the DNS service."
        #esto seria para poner en una interfaz
        #y seria el hook para arrancar el servicio
        pass

    @handler
    def stop(self):
        r"stop() -> None :: Stop the DNS service."
        #esto seria para poner en una interfaz
        #y seria el hook para arrancar el servicio
        pass

    @handler
    def restart(self):
        r"restart() -> None :: Restart the DNS service."
        #esto seria para poner en una interfaz
        #y seria el hook para arrancar el servicio
        pass

    @handler
    def reload(self):
        r"reload() -> None :: Reload the configuration of the DNS service."
        #esto seria para poner en una interfaz
        #y seria el hook para arrancar el servicio
        pass

    @handler
    def commit(self):
        r"commit() -> None :: Commit the changes and reload the DNS service."
        #esto seria para poner en una interfaz
        #y seria que hace el pickle deberia llamarse
        #al hacerse un commit
        self._dump()
        self._write_config()
        self.reload()

    @handler
    def rollback(self):
        r"rollback() -> None :: Discard the changes not yet commited."
        self._load()

    def _dump(self):
        r"_dump() -> None :: Dump all persistent data to pickle files."
        # XXX podría ir en una clase base
        self._dump_var(self.vars, pickle_vars)
        self._dump_var(self.zones, pickle_zones)

    def _load(self):
        r"_load() -> None :: Load all persistent data from pickle files."
        # XXX podría ir en una clase base
        self.vars = self._load_var(pickle_vars)
        self.zones = self._load_var(pickle_zones)

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
        # XXX podría ir en una clase base, ver como generalizar variables a
        # reemplazar en la template
        #archivos de zona
        delete_zones = list()
        for a_zone in self.zones.values():
            if a_zone.mod:
                # TODO freeze de la zona
                zone_out_file = file(path.join(self.config_dir, a_zone.name + zone_filename_ext), 'w')
                ctx = Context(
                    zone_out_file,
                    zone = a_zone,
                    hosts = a_zone.hosts.values(),
                    mxs = a_zone.mxs.values(),
                    nss = a_zone.nss.values()
                    )
                self.zone_template.render_context(ctx)
                zone_out_file.close()
                a_zone.mod = False
                # TODO unfreeze de la zona
            if a_zone.dele:
                #borro el archivo .zone
                try:
                    unlink(path.join(self.config_dir, a_zone.name + zone_filename_ext))
                except OSError:
                    #la excepcion pude darse en caso que haga un add de una zona y
                    #luego el del, como no hice commit, no se crea el archivo
                    pass
                delete_zones.append(a_zone.name)
        #borro las zonas
        for z in delete_zones:
            del self.zones[z]
        #archivo general
        cfg_out_file = file(path.join(self.config_dir, config_filename), 'w')
        ctx = Context(cfg_out_file, zones=self.zones.values(), **self.vars)
        self.config_template.render_context(ctx)
        cfg_out_file.close()



if __name__ == '__main__':

    dns = DnsHandler();

    dns.set('isp_dns1','la_garcha.com')
    dns.set('bind_addr1','localhost')
    dns.zone.add('zona_loca.com','ns1,dom.com','ns2.dominio.com')
    dns.zone.update('zona_loca.com','ns1.dominio.com')

    dns.host.add('zona_loca.com','hostname_loco','192.168.0.23')
    dns.host.update('zona_loca.com','hostname_loco','192.168.0.66')

    dns.host.add('zona_loca.com','hostname_kuak','192.168.0.23')
    dns.host.delete('zona_loca.com','hostname_kuak')

    dns.host.add('zona_loca.com','hostname_kuang','192.168.0.24')
    dns.host.add('zona_loca.com','hostname_chan','192.168.0.25')
    dns.host.add('zona_loca.com','hostname_kaine','192.168.0.26')

    dns.mx.add('zona_loca.com','mx1.sarasa.com',10)
    dns.mx.update('zona_loca.com','mx1.sarasa.com',20)
    dns.mx.add('zona_loca.com','mx2.sarasa.com',30)
    dns.mx.add('zona_loca.com','mx3.sarasa.com',40)
    dns.mx.delete('zona_loca.com','mx3.sarasa.com')

    dns.ns.add('zona_loca.com','ns1.jua.com')
    dns.ns.add('zona_loca.com','ns2.jua.com')
    dns.ns.add('zona_loca.com','ns3.jua.com')
    dns.ns.delete('zona_loca.com','ns3.jua.com')

    dns.zone.add('zona_oscura','ns1.lala.com')

    dns.host.add('zona_oscura','hostname_a','192.168.0.24')
    dns.host.add('zona_oscura','hostname_b','192.168.0.25')
    dns.host.add('zona_oscura','hostname_c','192.168.0.26')

    dns.zone.delete('zona_oscura')

    dns.commit()

    print 'ZONAS :'
    print dns.zone.show() + '\n'
    print 'HOSTS :'
    print dns.host.show()

    #test zone errors
    try:
        dns.zone.update('zone-sarasa','lalal')
    except ZoneNotFoundError, inst:
        print 'Error: ', inst

    try:
        dns.zone.delete('zone-sarasa')
    except ZoneNotFoundError, inst:
        print 'Error: ', inst

    try:
        dns.zone.add('zona_loca.com','ns1.dom.com','ns2.dom.com')
    except ZoneAlreadyExistsError, inst:
        print 'Error: ', inst

    #test hosts errors
    try:
        dns.host.update('zone-sarasa','kuak','192.68')
    except ZoneNotFoundError, inst:
        print 'Error: ', inst

    try:
        dns.host.update('zona_loca.com','kuak','192.68')
    except HostNotFoundError, inst:
        print 'Error: ', inst

    try:
        dns.host.delete('zone-sarasa','lala')
    except ZoneNotFoundError, inst:
        print 'Error: ', inst

    try:
        dns.host.delete('zona_loca.com','lala')
    except HostNotFoundError, inst:
        print 'Error: ', inst

    try:
        dns.host.add('zona','hostname_loco','192.168.0.23')
    except ZoneNotFoundError, inst:
        print 'Error: ', inst

    try:
        dns.host.add('zona_loca.com','hostname_loco','192.168.0.23')
    except HostAlreadyExistsError, inst:
        print 'Error: ', inst

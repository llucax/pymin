# vim: set encoding=utf-8 et sw=4 sts=4 :

# TODO COMMENT
from os import path
from os import unlink
from new import instancemethod

from seqtools import Sequence
from dispatcher import handler, HandlerError, Handler
from services.util import Restorable, ConfigWriter, call
from services.util import InitdHandler, TransactionalHandler, ParametersHandler

__ALL__ = ('DnsHandler', 'Error',
            'ZoneError', 'ZoneNotFoundError', 'ZoneAlreadyExistsError',
            'HostError', 'HostAlreadyExistsError', 'HostNotFoundError',
            'MailExchangeError', 'MailExchangeAlreadyExistsError',
            'MailExchangeNotFoundError', 'NameServerError',
            'NameServerAlreadyExistsError', 'NameServerNotFoundError')

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

class ZoneError(Error, KeyError):
    r"""
    ZoneError(zonename) -> ZoneError instance

    This is the base exception for all zone related errors.
    """

    def __init__(self, zonename):
        r"Initialize the object. See class documentation for more info."
        self.message = 'Zone error: "%s"' % zonename


class ZoneNotFoundError(ZoneError):
    r"""
    ZoneNotFoundError(hostname) -> ZoneNotFoundError instance

    This exception is raised when trying to operate on a zone that doesn't
    exists.
    """

    def __init__(self, zonename):
        r"Initialize the object. See class documentation for more info."
        self.message = 'zone not found: "%s"' % zonename


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
    MailExchangeError(hostname) -> MailExchangeError instance

    This is the base exception for all mail exchange related errors.
    """

    def __init__(self, mx):
        r"Initialize the object. See class documentation for more info."
        self.message = 'Mail Exchange error: "%s"' % mx


class MailExchangeAlreadyExistsError(MailExchangeError):
    r"""
    MailExchangeAlreadyExistsError(hostname) -> MailExchangeAlreadyExistsError instance

    This exception is raised when trying to add a mail exchange that already exists.
    """

    def __init__(self, mx):
        r"Initialize the object. See class documentation for more info."
        self.message = 'Mail Exchange already exists: "%s"' % mx


class MailExchangeNotFoundError(MailExchangeError):
    r"""
    MailExchangeNotFoundError(hostname) -> MailExchangeNotFoundError instance

    This exception is raised when trying to operate on a mail exchange that doesn't
    exists.
    """

    def __init__(self, mx):
        r"Initialize the object. See class documentation for more info."
        self.message = 'Mail Exchange not found: "%s"' % mx



class NameServerError(Error, KeyError):
    r"""
    NameServerError(ns) -> NameServerError instance

    This is the base exception for all name server related errors.
    """

    def __init__(self, ns):
        r"Initialize the object. See class documentation for more info."
        self.message = 'Name Server error: "%s"' % ns

class NameServerAlreadyExistsError(NameServerError):
    r"""
    NameServerAlreadyExistsError(hostname) -> NameServerAlreadyExistsError instance

    This exception is raised when trying to add a name server that already exists.
    """

    def __init__(self, ns):
        r"Initialize the object. See class documentation for more info."
        self.message = 'Name server already exists: "%s"' % ns

class NameServerNotFoundError(NameServerError):
    r"""
    NameServerNotFoundError(hostname) -> NameServerNotFoundError instance

    This exception is raised when trying to operate on a name server that doesn't
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

class Host(Sequence):
    def __init__(self, name, ip):
        self.name = name
        self.ip = ip

    def as_tuple(self):
        return (self.name, self.ip)

class HostHandler(Handler):
    def __init__(self,zones):
        self.zones = zones

    @handler(u'Adds a host to a zone')
    def add(self, name, hostname, ip):
        if not name in self.zones:
            raise ZoneNotFoundError(name)
        if hostname in self.zones[name].hosts:
            raise HostAlreadyExistsError(hostname)
        self.zones[name].hosts[hostname] = Host(hostname, ip)
        self.zones[name].mod = True

    @handler(u'Updates a host ip in a zone')
    def update(self, name, hostname, ip):
        if not name in self.zones:
            raise ZoneNotFoundError(name)
        if not hostname in self.zones[name].hosts:
             raise HostNotFoundError(name)
        self.zones[name].hosts[hostname].ip = ip
        self.zones[name].mod = True

    @handler(u'Deletes a host from a zone')
    def delete(self, name, hostname):
        if not name in self.zones:
            raise ZoneNotFoundError(name)
        if not hostname in self.zones[name].hosts:
             raise HostNotFoundError(name)
        del self.zones[name].hosts[hostname]
        self.zones[name].mod = True

    @handler(u'Lists hosts')
    def list(self):
        return self.zones.keys()

    @handler(u'Get insormation about all hosts')
    def show(self):
        return self.zones.values()


class MailExchange(Sequence):

    def __init__(self, mx, prio):
        self.mx = mx
        self.prio = prio

    def as_tuple(self):
        return (self.mx, self.prio)

class MailExchangeHandler(Handler):

    def __init__(self, zones):
        self.zones = zones

    @handler(u'Adds a mail exchange to a zone')
    def add(self, zonename, mx, prio):
        if not zonename in self.zones:
            raise ZoneNotFoundError(zonename)
        if mx in self.zones[zonename].mxs:
            raise MailExchangeAlreadyExistsError(mx)
        self.zones[zonename].mxs[mx] = MailExchange(mx, prio)
        self.zones[zonename].mod = True

    @handler(u'Updates a mail exchange priority')
    def update(self, zonename, mx, prio):
        if not zonename in self.zones:
            raise ZoneNotFoundError(zonename)
        if not mx in self.zones[zonename].mxs:
            raise MailExchangeNotFoundError(mx)
        self.zones[zonename].mxs[mx].prio = prio
        self.zones[zonename].mod = True

    @handler(u'Deletes a mail exchange from a zone')
    def delete(self, zonename, mx):
        if not zonename in self.zones:
            raise ZoneNotFoundError(zonename)
        if not mx in self.zones[zonename].mxs:
            raise MailExchangeNotFoundError(mx)
        del self.zones[zonename].mxs[mx]
        self.zones[zonename].mod = True

    @handler(u'Lists mail exchangers')
    def list(self):
        return self.zones.keys()

    @handler(u'Get information about all mail exchangers')
    def show(self):
        return self.zones.values()


class NameServer(Sequence):

    def __init__(self, name):
        self.name = name

    def as_tuple(self):
        return (self.name)

class NameServerHandler(Handler):

    def __init__(self, zones):
        self.zones = zones

    @handler(u'Adds a name server to a zone')
    def add(self, zone, ns):
        if not zone in self.zones:
            raise ZoneNotFoundError(zone)
        if ns in self.zones[zone].nss:
            raise NameServerAlreadyExistsError(ns)
        self.zones[zone].nss[ns] = NameServer(ns)
        self.zones[zone].mod = True

    @handler(u'Deletes a name server from a zone')
    def delete(self, zone, ns):
        if not zone in self.zones:
            raise ZoneNotFoundError(zone)
        if not ns in self.zones[zone].nss:
            raise NameServerNotFoundError(ns)
        del self.zones[zone].nss[ns]
        self.zones[zone].mod = True

    @handler(u'Lists name servers')
    def list(self):
        return self.zones.keys()

    @handler(u'Get information about all name servers')
    def show(self):
        return self.zones.values()


class Zone(Sequence):
    def __init__(self, name):
        self.name = name
        self.hosts = dict()
        self.mxs = dict()
        self.nss = dict()
        self.new = False
        self.mod = False
        self.dele = False

    def as_tuple(self):
        return (self.name, self.hosts, self.mxs, self.nss)

class ZoneHandler(Handler):

    r"""ZoneHandler(zones) -> ZoneHandler instance :: Handle a list of zones.

    This class is a helper for DnsHandler to do all the work related to zone
    administration.

    zones - A dictionary with string keys (zone name) and Zone instances values.
    """
    def __init__(self, zones):
        self.zones = zones

    @handler(u'Adds a zone')
    def add(self, name):
        if name in self.zones:
            if self.zones[name].dele == True:
                self.zones[name].dele = False
            else:
                raise ZoneAlreadyExistsError(name)
        self.zones[name] = Zone(name)
        self.zones[name].mod = True
        self.zones[name].new = True


    @handler(u'Deletes a zone')
    def delete(self, name):
        r"delete(name) -> None :: Delete a zone from the zone list."
        if not name in self.zones:
            raise ZoneNotFoundError(name)
        self.zones[name].dele = True

    @handler(u'Lists zones')
    def list(self):
        return self.zones.keys()

    @handler(u'Get information about all zones')
    def show(self):
        return self.zones.values()

class DnsHandler(Restorable, ConfigWriter, InitdHandler, TransactionalHandler,
                 ParametersHandler):
    r"""DnsHandler([pickle_dir[, config_dir]]) -> DnsHandler instance.

    Handles DNS service commands for the dns program.

    pickle_dir - Directory where to write the persistent configuration data.

    config_dir - Directory where to store de generated configuration files.

    Both defaults to the current working directory.
    """

    _initd_name = 'bind'

    _persistent_vars = ('params', 'zones')

    _restorable_defaults = dict(
            zones = dict(),
            params  = dict(
                isp_dns1 = '',
                isp_dns2 = '',
                bind_addr1 = '',
                bind_addr2 = ''
            ),
    )

    _config_writer_files = ('named.conf', 'zoneX.zone')
    _config_writer_tpl_dir = path.join(path.dirname(__file__), 'templates')

    def __init__(self, pickle_dir='.', config_dir='.'):
        r"Initialize DnsHandler object, see class documentation for details."
        self._persistent_dir = pickle_dir
        self._config_writer_cfg_dir = config_dir
        self.mod = False
        self._config_build_templates()
        self._restore()
        self.host = HostHandler(self.zones)
        self.zone = ZoneHandler(self.zones)
        self.mx = MailExchangeHandler(self.zones)
        self.ns = NameServerHandler(self.zones)

    def _zone_filename(self, zone):
        return zone.name + '.zone'

    def _get_config_vars(self, config_file):
        return dict(zones=self.zones.values(), **self.params)

    def _write_config(self):
        r"_write_config() -> None :: Generate all the configuration files."
        delete_zones = list()
        for a_zone in self.zones.values():
            if a_zone.mod:
                if not a_zone.new:
                    # TODO freeze de la zona
                    call(('dns', 'freeze', a_zone.name))
                vars = dict(
                    zone = a_zone,
                    hosts = a_zone.hosts.values(),
                    mxs = a_zone.mxs.values(),
                    nss = a_zone.nss.values()
                )
                self._write_single_config('zoneX.zone',
                                            self._zone_filename(a_zone), vars)
                a_zone.mod = False
                if not a_zone.new:
                    # TODO unfreeze de la zona
                    call(('dns', 'unfreeze', a_zone.name))
                else :
                    self.mod = True
                    a_zone.new = False
            if a_zone.dele:
                #borro el archivo .zone
                try:
                    self.mod = True
                    unlink(self._zone_filename(a_zone))
                except OSError:
                    #la excepcion pude darse en caso que haga un add de una zona y
                    #luego el del, como no hice commit, no se crea el archivo
                    pass
                delete_zones.append(a_zone.name)
        #borro las zonas
        for z in delete_zones:
            del self.zones[z]
        #archivo general
        if self.mod:
            self._write_single_config('named.conf')
            self.mod = False
            self.reload()

if __name__ == '__main__':

    dns = DnsHandler();

    dns.set('isp_dns1','la_garcha.com')
    dns.set('bind_addr1','localhost')
    dns.zone.add('zona_loca.com')
    #dns.zone.update('zona_loca.com','ns1.dominio.com')

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

    dns.zone.add('zona_oscura')

    dns.host.add('zona_oscura','hostname_a','192.168.0.24')
    dns.host.add('zona_oscura','hostname_b','192.168.0.25')
    dns.host.add('zona_oscura','hostname_c','192.168.0.26')

    dns.zone.delete('zona_oscura')

    dns.commit()

    print 'ZONAS :', dns.zone.show()
    print 'HOSTS :', dns.host.show()

    #test zone errors
    #try:
    #    dns.zone.update('zone-sarasa','lalal')
    #except ZoneNotFoundError, inst:
    #    print 'Error: ', inst

    try:
        dns.zone.delete('zone-sarasa')
    except ZoneNotFoundError, inst:
        print 'Error: ', inst

    #try:
    #    dns.zone.add('zona_loca.com','ns1.dom.com','ns2.dom.com')
    #except ZoneAlreadyExistsError, inst:
    #    print 'Error: ', inst

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

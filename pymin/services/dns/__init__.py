# vim: set encoding=utf-8 et sw=4 sts=4 :

# TODO COMMENT
from os import path
from os import unlink
import logging ; log = logging.getLogger('pymin.services.dns')

from pymin.seqtools import Sequence
from pymin.dispatcher import handler, HandlerError, Handler
from pymin.services.util import Restorable, ConfigWriter, InitdHandler, \
                                TransactionalHandler, ParametersHandler, \
                                DictComposedSubHandler, DictSubHandler, call

__all__ = ('DnsHandler',)

class Host(Sequence):
    def __init__(self, name, ip):
        self.name = name
        self.ip = ip
    def update(self, ip=None):
        if ip is not None: self.ip = ip
    def as_tuple(self):
        return (self.name, self.ip)

class HostHandler(DictComposedSubHandler):
    handler_help = u"Manage DNS hosts"
    _comp_subhandler_cont = 'zones'
    _comp_subhandler_attr = 'hosts'
    _comp_subhandler_class = Host

class MailExchange(Sequence):
    def __init__(self, mx, prio):
        self.mx = mx
        self.prio = prio
    def update(self, prio=None):
        if prio is not None: self.prio = prio
    def as_tuple(self):
        return (self.mx, self.prio)

class MailExchangeHandler(DictComposedSubHandler):
    handler_help = u"Manage DNS mail exchangers (MX)"
    _comp_subhandler_cont = 'zones'
    _comp_subhandler_attr = 'mxs'
    _comp_subhandler_class = MailExchange

class NameServer(Sequence):
    def __init__(self, name):
        self.name = name
    def as_tuple(self):
        return (self.name,)

class NameServerHandler(DictComposedSubHandler):
    handler_help = u"Manage DNS name servers (NS)"
    _comp_subhandler_cont = 'zones'
    _comp_subhandler_attr = 'nss'
    _comp_subhandler_class = NameServer

class Zone(Sequence):
    def __init__(self, name):
        self.name = name
        self.hosts = dict()
        self.mxs = dict()
        self.nss = dict()
        self._add = False
        self._update = False
        self._delete = False
    def as_tuple(self):
        return (self.name, self.hosts, self.mxs, self.nss)

class ZoneHandler(DictSubHandler):
    handler_help = u"Manage DNS zones"
    _cont_subhandler_attr = 'zones'
    _cont_subhandler_class = Zone

class DnsHandler(Restorable, ConfigWriter, InitdHandler, TransactionalHandler,
                 ParametersHandler):
    r"""DnsHandler([pickle_dir[, config_dir]]) -> DnsHandler instance.

    Handles DNS service commands for the dns program.

    pickle_dir - Directory where to write the persistent configuration data.

    config_dir - Directory where to store de generated configuration files.

    Both defaults to the current working directory.
    """

    handler_help = u"Manage DNS service"

    _initd_name = 'named'

    _persistent_attrs = ('params', 'zones')

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
        log.debug(u'DnsHandler(%r, %r)', pickle_dir, config_dir)
        self._persistent_dir = pickle_dir
        self._config_writer_cfg_dir = config_dir
        self._update = False
        self._config_build_templates()
        InitdHandler.__init__(self)
        self.host = HostHandler(self)
        self.zone = ZoneHandler(self)
        self.mx = MailExchangeHandler(self)
        self.ns = NameServerHandler(self)

    def _zone_filename(self, zone):
        return zone.name + '.zone'

    def _get_config_vars(self, config_file):
        return dict(zones=self.zones.values(), **self.params)

    def _write_config(self):
        r"_write_config() -> None :: Generate all the configuration files."
        log.debug(u'DnsHandler._write_config()')
        delete_zones = list()
        for a_zone in self.zones.values():
            log.debug(u'DnsHandler._write_config: processing zone %s', a_zone)
            if a_zone._update or a_zone._add:
                if not a_zone._add and self._service_running:
                    log.debug(u'DnsHandler._write_config: zone updated and '
                                u'the service is running, freezing zone')
                    call(('rndc', 'freeze', a_zone.name))
                vars = dict(
                    zone = a_zone,
                    hosts = a_zone.hosts.values(),
                    mxs = a_zone.mxs.values(),
                    nss = a_zone.nss.values()
                )
                self._write_single_config('zoneX.zone',
                                            self._zone_filename(a_zone), vars)
                a_zone._update = False
                if not a_zone._add and self._service_running:
                    log.debug(u'DnsHandler._write_config: unfreezing zone')
                    call(('rndc', 'thaw', a_zone.name))
                else :
                    self._update = True
                    a_zone._add = False
            if a_zone._delete:
                #borro el archivo .zone
                log.debug(u'DnsHandler._write_config: zone deleted, removing '
                            u'the file %r', self._zone_filename(a_zone))
                try:
                    self._update = True
                    unlink(self._zone_filename(a_zone))
                except OSError:
                    #la excepcion pude darse en caso que haga un add de una zona y
                    #luego el del, como no hice commit, no se crea el archivo
                    log.debug(u'DnsHandler._write_config: file not found')
                    pass
                delete_zones.append(a_zone.name)
        #borro las zonas
        for z in delete_zones:
            del self.zones[z]
        #archivo general
        if self._update:
            self._write_single_config('named.conf')
            self._update = False
            return False # Do reload
        return True # we don't need to reload

    # HACK!!!!
    def handle_timer(self):
        log.debug(u'DnsHandler.handle_timer()')
        import subprocess
        p = subprocess.Popen(('pgrep', '-f', '/usr/sbin/named'),
                                stdout=subprocess.PIPE)
        pid = p.communicate()[0]
        if p.returncode == 0 and len(pid) > 0:
            log.debug(u'DnsHandler.handle_timer: pid present, running')
            self._service_running = True
        else:
            log.debug(u'DnsHandler.handle_timer: pid absent, NOT running')
            self._service_running = False



if __name__ == '__main__':

    logging.basicConfig(
        level   = logging.DEBUG,
        format  = '%(asctime)s %(levelname)-8s %(message)s',
        datefmt = '%H:%M:%S',
    )

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
    for z in dns.zones:
        print 'HOSTS from', z, ':', dns.host.show(z)

    #test zone errors
    #try:
    #    dns.zone.update('zone-sarasa','lalal')
    #except ZoneNotFoundError, inst:
    #    print 'Error: ', inst

    from pymin.services.util import ItemNotFoundError, ItemAlreadyExistsError, \
                                    ContainerNotFoundError

    try:
        dns.zone.delete('zone-sarasa')
    except ItemNotFoundError, inst:
        print 'Error: ', inst

    #try:
    #    dns.zone.add('zona_loca.com','ns1.dom.com','ns2.dom.com')
    #except ZoneAlreadyExistsError, inst:
    #    print 'Error: ', inst


    #test hosts errors
    try:
        dns.host.update('zone-sarasa','kuak','192.68')
    except ContainerNotFoundError, inst:
        print 'Error: ', inst

    try:
        dns.host.update('zona_loca.com','kuak','192.68')
    except ItemNotFoundError, inst:
        print 'Error: ', inst

    try:
        dns.host.delete('zone-sarasa','lala')
    except ContainerNotFoundError, inst:
        print 'Error: ', inst

    try:
        dns.host.delete('zona_loca.com','lala')
    except ItemNotFoundError, inst:
        print 'Error: ', inst

    try:
        dns.host.add('zona','hostname_loco','192.168.0.23')
    except ContainerNotFoundError, inst:
        print 'Error: ', inst

    try:
        dns.host.add('zona_loca.com','hostname_loco','192.168.0.23')
    except ItemAlreadyExistsError, inst:
        print 'Error: ', inst

# vim: set encoding=utf-8 et sw=4 sts=4 :

from os import path
import logging ; log = logging.getLogger('pymin.services.dhcp')

from pymin.service.util import Restorable, ConfigWriter, ReloadHandler, \
                               TransactionalHandler, ParametersHandler, \
                               InitdHandler

from host import HostHandler

__all__ = ('DhcpHandler',)

class DhcpHandler(Restorable, ConfigWriter, ReloadHandler, TransactionalHandler,
                  ParametersHandler, InitdHandler):
    r"""DhcpHandler([pickle_dir[, config_dir]]) -> DhcpHandler instance.

    Handles DHCP service commands for the dhcpd program.

    pickle_dir - Directory where to write the persistent configuration data.

    config_dir - Directory where to store de generated configuration files.

    Both defaults to the current working directory.
    """

    handler_help = u"Manage DHCP service"

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
        log.debug(u'DhcpHandler(%r, %r)', pickle_dir, config_dir)
        self._persistent_dir = pickle_dir
        self._config_writer_cfg_dir = config_dir
        self._config_build_templates()
        InitdHandler.__init__(self)
        self.host = HostHandler(self)

    def _get_config_vars(self, config_file):
        return dict(hosts=self.hosts.values(), **self.params)


if __name__ == '__main__':

    logging.basicConfig(
        level   = logging.DEBUG,
        format  = '%(asctime)s %(levelname)-8s %(message)s',
        datefmt = '%H:%M:%S',
    )

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


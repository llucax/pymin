# vim: set encoding=utf-8 et sw=4 sts=4 :

from formencode import validators as V
from pymin.config import Option
from handler import DnsHandler

def setup_service(options, config):
    options.add_group('dns', 'DNS service', [
        Option('pickle_dir', V.String, metavar='DIR',
               help='store persistent data in DIR directory'),
        Option('config_named_dir', V.String, metavar='DIR',
               help='write named config files in DIR directory'),
        Option('config_zones_dir', V.String, metavar='DIR',
               help='write zone config files in DIR directory'),
    ])

def get_service(config):
    return DnsHandler(config.dns.pickle_dir, {
                'named.conf': config.dns.config_named_dir,
                'zoneX.zone': config.dns.config_zones_dir,
    })


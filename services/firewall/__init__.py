# vim: set encoding=utf-8 et sw=4 sts=4 :

from formencode import validators as V
from pymin.config import Option
from handler import FirewallHandler

def setup_service(options, config):
    options.add_group('firewall', 'Firewall service', [
        Option('pickle_dir', V.String, metavar='DIR',
               help='store persistent data in DIR directory'),
        Option('config_dir', V.String, metavar='DIR',
               help='write config file in DIR directory'),
    ])

def get_service(config):
    return FirewallHandler(config.firewall.pickle_dir, config.firewall.config_dir)


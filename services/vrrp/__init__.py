# vim: set encoding=utf-8 et sw=4 sts=4 :

from formencode import validators as V
from pymin.config import Option
from handler import VrrpHandler

def setup_service(options, config):
    options.add_group('vrrp', 'Virtual Router Redundancy service', [
        Option('pickle_dir', V.String, metavar='DIR',
               help='store persistent data in DIR directory'),
        Option('config_dir', V.String, metavar='DIR',
               help='write config file in DIR directory'),
        Option('pid_dir', V.String, metavar='DIR',
               help='write PID file in DIR directory'),
    ])

def get_service(config):
    return VrrpHandler(config.vrrp.pickle_dir, config.vrrp.config_dir,
                       config.vrrp.pid_dir)


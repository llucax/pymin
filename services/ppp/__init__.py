# vim: set encoding=utf-8 et sw=4 sts=4 :

from formencode import validators as V
from pymin.config import Option
from handler import PppHandler

def setup_service(options, config):
    options.add_group('ppp', 'PPP network interfaces', [
        Option('pickle_dir', V.String, metavar='DIR',
               help='store persistent data in DIR directory'),
        Option('config_options_dir', V.String, metavar='DIR',
               help='write options config files in DIR directory'),
        Option('config_pap_dir', V.String, metavar='DIR',
               help='write pap-secrets config file in DIR directory'),
        Option('config_chap_dir', V.String, metavar='DIR',
               help='write chap-secrets config file in DIR directory'),
        Option('config_peers_dir', V.String, metavar='DIR',
               help='write peer config files in DIR directory'),
    ])

def get_service(config):
    return PppHandler(config.ppp.pickle_dir, {
                'options.X': config.ppp.config_options_dir,
                'pap-secrets': config.ppp.config_pap_dir,
                'chap-secrets': config.ppp.config_chap_dir,
                'nameX': config.ppp.config_peers_dir,
    })


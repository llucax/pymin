# vim: set encoding=utf-8 et sw=4 sts=4 :

from formencode import validators as V
from pymin.config import Option
from handler import QoSHandler

def setup_service(options, config):
    options.add_group('qos', 'Quality of Service', [
        Option('pickle_dir', V.String, metavar='DIR',
               help='store persistent data in DIR directory'),
        Option('config_dir', V.String, metavar='DIR',
               help='write config files in DIR directory'),
    ])

def get_service(config):
    return QoSHandler(config.qos.pickle_dir, config.qos.config_dir)


# vim: set encoding=utf-8 et sw=4 sts=4 :

from formencode import validators as V
from pymin.config import Option
from handler import NatHandler

def setup_service(options, config):
    options.add_group('nat', 'Network Address Translation service', [
        Option('pickle_dir', V.String, metavar='DIR',
               help='store persistent data in DIR directory'),
    ])

def get_service(config):
    return NatHandler(config.nat.pickle_dir)


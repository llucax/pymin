# vim: set encoding=utf-8 et sw=4 sts=4 :

from handler import NatHandler

def get_service(config):
    return NatHandler(config.nat.pickle_dir)


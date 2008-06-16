# vim: set encoding=utf-8 et sw=4 sts=4 :

from handler import PppHandler

def get_service(config):
    return PppHandler(config.ppp.pickle_dir, config.ppp.config_dir)


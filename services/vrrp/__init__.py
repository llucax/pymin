# vim: set encoding=utf-8 et sw=4 sts=4 :

from handler import VrrpHandler

def get_service(config):
    return VrrpHandler(config.vrrp.pickle_dir, config.vrrp.config_dir)


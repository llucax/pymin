# vim: set encoding=utf-8 et sw=4 sts=4 :

from handler import VpnHandler

def get_service(config):
    return VpnHandler(config.vpn.pickle_dir, config.vpn.config_dir)


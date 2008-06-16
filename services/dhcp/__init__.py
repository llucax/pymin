# vim: set encoding=utf-8 et sw=4 sts=4 :

from handler import DhcpHandler

def get_service(config):
    return DhcpHandler(config.dhcp.pickle_dir, config.dhcp.config_dir)


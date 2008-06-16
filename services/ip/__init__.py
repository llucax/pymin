# vim: set encoding=utf-8 et sw=4 sts=4 :

from handler import IpHandler

def get_service(config):
    return IpHandler(config.ip.pickle_dir, config.ip.config_dir)


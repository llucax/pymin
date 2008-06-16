# vim: set encoding=utf-8 et sw=4 sts=4 :

from handler import ProxyHandler

def get_service(config):
    return ProxyHandler(config.proxy.pickle_dir, config.proxy.config_dir)


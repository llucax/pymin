# vim: set encoding=utf-8 et sw=4 sts=4 :

from handler import FirewallHandler

def get_service(config):
    return FirewallHandler(config.firewall.pickle_dir, config.firewall.config_dir)


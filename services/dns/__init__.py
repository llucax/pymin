# vim: set encoding=utf-8 et sw=4 sts=4 :

from handler import DnsHandler

def get_service(config):
    return DnsHandler(config.dns.pickle_dir, config.dns.config_dir)


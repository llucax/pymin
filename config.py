# vim: set et sts=4 sw=4 encoding=utf-8 :

from pymin.services import *
from pymin.dispatcher import Handler
from os.path import join

base_path = join('var', 'lib', 'pymin')
pickle_path = join(base_path, 'pickle')
# FIXME, this should be specific for each service
config_path = join(base_path, 'config')

class Root(Handler):
    ip = IpHandler(
        pickle_dir = join(pickle_path, 'ip'),
        config_dir = join(config_path, 'ip'))
    firewall = FirewallHandler(
        pickle_dir = join(pickle_path, 'firewall'),
        config_dir = join(config_path, 'firewall'))
    nat = NatHandler(pickle_dir = join(pickle_path, 'nat'))
    dns = DnsHandler(
        pickle_dir = join(pickle_path, 'dns'),
        config_dir = {
            'named.conf': join(config_path, 'dns'),
            'zoneX.zone': join(config_path, 'dns', 'zones'),
        })
    dhcp = DhcpHandler(
        pickle_dir = join(pickle_path, 'dhcp'),
        config_dir = join(config_path, 'dhcp'))
    ppp = PppHandler(
        pickle_dir = join(pickle_path, 'ppp'),
        config_dir = join(config_path, 'ppp'))
    vrrp = VrrpHandler(
        pickle_dir = join(pickle_path, 'vrrp'),
        config_dir = join(config_path, 'vrrp'))
    proxy = ProxyHandler(
        pickle_dir = join(pickle_path, 'proxy'),
        config_dir = join(config_path, 'proxy'))

bind_addr = \
(
    '',   # Bind IP ('' is ANY)
    9999, # Port
)


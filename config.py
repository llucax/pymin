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
        config_dir = '/tmp')

    dhcp = DhcpHandler(
        pickle_dir = join(pickle_path, 'dhcp'),
        config_dir = '/etc')

    dns = DnsHandler(
        pickle_dir = join(pickle_path, 'dns'),
        config_dir = {
            'named.conf': '/etc',
            'zoneX.zone': '/var/lib/named',
        })

    nat = NatHandler(pickle_dir = join(pickle_path, 'nat'))

    proxy = ProxyHandler(
        pickle_dir = join(pickle_path, 'proxy'),
        config_dir = '/etc/squid')

    vrrp = VrrpHandler(
        pickle_dir = join(pickle_path, 'vrrp'),
        config_dir = join(config_path, 'vrrp'),
        pid_dir    = '/var/run')

    ppp = PppHandler(
        pickle_dir = join(pickle_path, 'ppp'),
        config_dir = {
            'pap-secrets':  '/etc/ppp',
            'chap-secrets': '/etc/ppp',
            'options.X':    '/etc/ppp',
            'nameX':        '/etc/ppp/peers',
        })

bind_addr = \
(
    '',   # Bind IP ('' is ANY)
    9999, # Port
)


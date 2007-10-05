# vim: set et sts=4 sw=4 encoding=utf-8 :

from pymin.services import *
from pymin.dispatcher import Handler

class Root(Handler):
    dhcp = DhcpHandler(
        pickle_dir = 'var/lib/pymin/pickle/dhcp',
        config_dir = 'var/lib/pymin/config/dhcp')
    dns = DnsHandler(
        pickle_dir = 'var/lib/pymin/pickle/dns',
        config_dir = 'var/lib/pymin/config/dns')
    firewall = FirewallHandler(
        pickle_dir = 'var/lib/pymin/pickle/firewall',
        config_dir = 'var/lib/pymin/config/firewall')
    ip = IpHandler(
        pickle_dir = 'var/lib/pymin/pickle/ip',
        config_dir = 'var/lib/pymin/config/ip')
    proxy = ProxyHandler(
        pickle_dir = 'var/lib/pymin/pickle/proxy',
        config_dir = 'var/lib/pymin/config/proxy')

bind_addr = \
(
    '',   # Bind IP ('' is ANY)
    9999, # Port
)


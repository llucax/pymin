# vim: set et sts=4 sw=4 encoding=utf-8 :

from pymin.services import *
from pymin.dispatcher import Handler
from os.path import join

base_path = join('var', 'lib', 'pymin')
pickle_path = join(base_path, 'pickle')
# FIXME, this should be specific for each service
config_path = join(base_path, 'config')

class Root(Handler):

    def __init__(self):
        f = file("/proc/sys/net/ipv4/ip_forward","w")
        f.write("1")
        f.close()
        #self.ip.device_up_hook(self.dns)

    firewall = FirewallHandler(
        pickle_dir = join(pickle_path, 'firewall'),
        config_dir = '/tmp')

    nat = NatHandler(pickle_dir = join(pickle_path, 'nat'))

    ppp = PppHandler(
        pickle_dir = join(pickle_path, 'ppp'),
        config_dir = {
            'pap-secrets':  '/etc/ppp',
            'chap-secrets': '/etc/ppp',
            'options.X':    '/etc/ppp',
            'nameX':        '/etc/ppp/peers',
        })

    vpn = VpnHandler(
         pickle_dir = join(pickle_path, 'vpn'),
         config_dir = join(config_path, 'vpn'))

    ip = IpHandler(
        pickle_dir = join(pickle_path, 'ip'),
        config_dir = join(config_path, 'ip'))

    dns = DnsHandler(
        pickle_dir = join(pickle_path, 'dns'),
        config_dir = {
            'named.conf': '/etc',
            'zoneX.zone': '/var/lib/named',
        })

    dhcp = DhcpHandler(
        pickle_dir = join(pickle_path, 'dhcp'),
        config_dir = '/etc')

    proxy = ProxyHandler(
        pickle_dir = join(pickle_path, 'proxy'),
        config_dir = '/etc/squid')

    vrrp = VrrpHandler(
        pickle_dir = join(pickle_path, 'vrrp'),
        config_dir = join(config_path, 'vrrp'),
        pid_dir    = '/var/run')

    vpn = VpnHandler(
        pickle_dir = join(pickle_path, 'vpn'),
        config_dir = '/etc/tinc')

    #qos = QoSHandler(
    #    pickle_dir = join(pickle_path, 'qos'),
    #    config_dir = join(config_path, 'qos'))

bind_addr = \
(
    '',   # Bind IP ('' is ANY)
    9999, # Port
)


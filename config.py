# vim: set et sts=4 sw=4 encoding=utf-8 :

# First of all, we need to setup the logging framework
import logging
logging.basicConfig(
        level   = logging.DEBUG,
        format  = '%(asctime)s %(name)-18s %(levelname)-8s %(message)s',
        datefmt = '%a, %d %b %Y %H:%M:%S',
)

from pymin.services import *
from pymin.dispatcher import Handler
from os.path import join

base_path = join('var', 'lib', 'pymin')
pickle_path = join(base_path, 'pickle')
# FIXME, this should be specific for each service
config_path = join(base_path, 'config')

class Root(Handler):

    firewall = FirewallHandler(
        pickle_dir = join(pickle_path, 'firewall'),
        config_dir = join(config_path, 'firewall'))

    nat = NatHandler(pickle_dir = join(pickle_path, 'nat'))

    ppp = PppHandler(
        pickle_dir = join(pickle_path, 'ppp'),
        config_dir = {
            'pap-secrets':  join(config_path, 'ppp'),
            'chap-secrets': join(config_path, 'ppp'),
            'options.X':    join(config_path, 'ppp'),
            'nameX':        join(config_path, 'ppp', 'peers'),
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
            'named.conf': join(config_path, 'dns'),
            'zoneX.zone': join(config_path, 'dns', 'zones'),
        })

    dhcp = DhcpHandler(
        pickle_dir = join(pickle_path, 'dhcp'),
        config_dir = join(config_path, 'dhcp'))

    proxy = ProxyHandler(
        pickle_dir = join(pickle_path, 'proxy'),
        config_dir = join(config_path, 'proxy'))

    vrrp = VrrpHandler(
        pickle_dir = join(pickle_path, 'vrrp'),
        config_dir = join(config_path, 'vrrp'),
        pid_dir    = join(config_path, 'vrrp', 'run'))

    vpn = VpnHandler(
        pickle_dir = join(pickle_path, 'vpn'),
        config_dir = join(config_path, 'vpn'))

    #qos = QoSHandler(
    #    pickle_dir = join(pickle_path, 'qos'),
    #    config_dir = join(config_path, 'qos'))

bind_addr = \
(
    '',   # Bind IP ('' is ANY)
    9999, # Port
)


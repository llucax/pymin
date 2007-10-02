# vim: set et sts=4 sw=4 encoding=utf-8 :

from services import *
from dispatcher import handler

# XXX for testing only
@handler
def test_func(*args):
    print 'func:', args

routes = dict \
(
    dhcp = DhcpHandler(
        pickle_dir = 'var/lib/pymin/pickle/dhcp',
        config_dir = 'var/lib/pymin/config/dhcp',
    ),
    dns = DnsHandler(
        pickle_dir = 'var/lib/pymin/pickle/dns',
        config_dir = 'var/lib/pymin/config/dns',
    ),
    firewall = FirewallHandler(
        pickle_dir = 'var/lib/pymin/pickle/firewall',
        config_dir = 'var/lib/pymin/config/firewall',
    ),
)

bind_addr = \
(
    '',   # Bind IP ('' is ANY)
    9999, # Port
)


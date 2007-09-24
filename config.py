# vim: set et sts=4 sw=4 encoding=utf-8 :

from services import *

# XXX for testing only
def test_func(*args):
    print 'func:', args

routes = dict \
(
    test = test_func,
    dhcp = DhcpHandler(
        pickle_dir = 'var/lib/pymin/pickle/dhcp',
        config_dir = 'var/lib/pymin/config/dhcp',
    ),
)

bind_addr = \
(
    '',   # Bind IP ('' is ANY)
    9999, # Port
)


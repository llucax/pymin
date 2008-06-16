# vim: set et sts=4 sw=4 encoding=utf-8 :

# First of all, we need to setup the logging framework
import logging
logging.basicConfig(
        level   = logging.DEBUG,
        format  = '%(asctime)s %(name)-24s %(levelname)-8s %(message)s',
        datefmt = '%a, %d %b %Y %H:%M:%S',
)

from pymin.dispatcher import Handler
from os.path import join

base_path = join('var', 'lib', 'pymin')
pickle_path = join(base_path, 'pickle')
# FIXME, this should be specific for each service
config_path = join(base_path, 'config')

class firewall:
    pickle_dir = join(pickle_path, 'firewall')
    config_dir = join(config_path, 'firewall')

class nat:
    pickle_dir = join(pickle_path, 'nat')

class ppp:
    pickle_dir = join(pickle_path, 'ppp')
    config_dir = {
        'pap-secrets':  join(config_path, 'ppp'),
        'chap-secrets': join(config_path, 'ppp'),
        'options.X':    join(config_path, 'ppp'),
        'nameX':        join(config_path, 'ppp', 'peers'),
    }

class vpn:
     pickle_dir = join(pickle_path, 'vpn')
     config_dir = join(config_path, 'vpn')

class ip:
    pickle_dir = join(pickle_path, 'ip')
    config_dir = join(config_path, 'ip')

class dns:
    pickle_dir = join(pickle_path, 'dns')
    config_dir = {
        'named.conf': join(config_path, 'dns'),
        'zoneX.zone': join(config_path, 'dns', 'zones'),
    }

class dhcp:
    pickle_dir = join(pickle_path, 'dhcp')
    config_dir = join(config_path, 'dhcp')

class proxy:
    pickle_dir = join(pickle_path, 'proxy')
    config_dir = join(config_path, 'proxy')

class vrrp:
    pickle_dir = join(pickle_path, 'vrrp')
    config_dir = join(config_path, 'vrrp')
    pid_dir    = join(config_path, 'vrrp', 'run')

class vpn:
    pickle_dir = join(pickle_path, 'vpn')
    config_dir = join(config_path, 'vpn')

class qos:
    pickle_dir = join(pickle_path, 'qos')
    config_dir = join(config_path, 'qos')

bind_addr = \
(
    '',   # Bind IP ('' is ANY)
    9999, # Port
)

services = 'firewall nat ppp vpn ip dns dhcp proxy vrrp qos'.split()

services_dirs = ['services']


# vim: set encoding=utf-8 et sw=4 sts=4 :

from subprocess import Popen, PIPE
from os import path

from pymin.seqtools import Sequence
from pymin.dispatcher import handler, HandlerError, Handler
from pymin.services.util import Restorable, ConfigWriter, InitdHandler, \
                                TransactionalHandler, SubHandler, call, \
                                get_network_devices, ListComposedSubHandler, \
                                DictComposedSubHandler

__ALL__ = ('IpHandler',)

class Route(Sequence):
    def __init__(self, net_addr, prefix, gateway):
        self.net_addr = net_addr
        self.prefix = prefix
        self.gateway = gateway
    def update(self, net_addr=None, prefix=None, gateway=None):
        if net_addr is not None: self.net_addr = net_addr
        if prefix is not None: self.prefix = prefix
        if gateway is not None: self.gateway = gateway
    def as_tuple(self):
        return(self.net_addr, self.prefix, self.gateway)

class RouteHandler(ListComposedSubHandler):
    handler_help = u"Manage IP routes"
    _comp_subhandler_cont = 'devices'
    _comp_subhandler_attr = 'routes'
    _comp_subhandler_class = Route

class Address(Sequence):
    def __init__(self, ip, netmask, broadcast=None):
        self.ip = ip
        self.netmask = netmask
        self.broadcast = broadcast
    def update(self, netmask=None, broadcast=None):
        if netmask is not None: self.netmask = netmask
        if broadcast is not None: self.broadcast = broadcast
    def as_tuple(self):
        return (self.ip, self.netmask, self.broadcast)

class AddressHandler(DictComposedSubHandler):
    handler_help = u"Manage IP addresses"
    _comp_subhandler_cont = 'devices'
    _comp_subhandler_attr = 'addrs'
    _comp_subhandler_class = Address

class Device(Sequence):
    def __init__(self, name, mac):
        self.name = name
        self.mac = mac
        self.addrs = dict()
        self.routes = list()
    def as_tuple(self):
        return (self.name, self.mac)

class DeviceHandler(SubHandler):

    handler_help = u"Manage network devices"

    def __init__(self, parent):
        # FIXME remove templates to execute commands
        from mako.template import Template
        self.parent = parent
        template_dir = path.join(path.dirname(__file__), 'templates')
        dev_fn = path.join(template_dir, 'device')
        self.device_template = Template(filename=dev_fn)

    @handler(u'Bring the device up')
    def up(self, name):
        if name in self.parent.devices:
            call(self.device_template.render(dev=name, action='up'), shell=True)
        else:
            raise DeviceNotFoundError(name)

    @handler(u'Bring the device down')
    def down(self, name):
        if name in self.parent.devices:
            call(self.device_template.render(dev=name, action='down'), shell=True)
        else:
            raise DeviceNotFoundError(name)

    @handler(u'List all devices')
    def list(self):
        return self.parent.devices.keys()

    @handler(u'Get information about a device')
    def show(self):
        return self.parent.devices.items()

class IpHandler(Restorable, ConfigWriter, TransactionalHandler):

    handler_help = u"Manage IP devices, addresses and routes"

    _persistent_attrs = 'devices'

    _restorable_defaults = dict(devices=dict((dev, Device(dev, mac))
                            for (dev, mac) in get_network_devices().items()))

    _config_writer_files = ('device', 'ip_add', 'ip_del', 'ip_flush',
                            'route_add', 'route_del', 'route_flush')
    _config_writer_tpl_dir = path.join(path.dirname(__file__), 'templates')

    def __init__(self, pickle_dir='.', config_dir='.'):
        r"Initialize DhcpHandler object, see class documentation for details."
        self._persistent_dir = pickle_dir
        self._config_writer_cfg_dir = config_dir
        self._config_build_templates()
        self._restore()
        self.addr = AddressHandler(self)
        self.route = RouteHandler(self)
        self.dev = DeviceHandler(self)

    def _write_config(self):
        r"_write_config() -> None :: Execute all commands."
        for device in self.devices.values():
            call(self._render_config('route_flush', dict(dev=device.name)), shell=True)
            call(self._render_config('ip_flush', dict(dev=device.name)), shell=True)
            for address in device.addrs.values():
                call(self._render_config('ip_add', dict(
                        dev = device.name,
                        addr = address.ip,
                        netmask = address.netmask,
                        broadcast = address.broadcast,
                    )
                ), shell=True)
            for route in device.routes:
                call(self._render_config('route_add', dict(
                        dev = device.name,
                        net_addr = route.net_addr,
                        prefix = route.prefix,
                        gateway = route.gateway,
                    )
                ), shell=True)


if __name__ == '__main__':

    ip = IpHandler()
    print '----------------------'
    ip.dev.up('eth0')
    ip.addr.add('eth0','192.168.0.23','24','192.168.255.255')
    ip.addr.add('eth0','192.168.0.26','24')
    ip.commit()
    ip.route.add('eth0','192.168.0.0','24','192.168.0.1')
    ip.route.add('eth0','192.168.0.5','24','192.168.0.1')
    ip.commit()
    ip.route.clear('eth0')
    ip.commit()
    ip.addr.delete('eth0','192.168.0.23')
    ip.commit()





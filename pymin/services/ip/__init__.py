# vim: set encoding=utf-8 et sw=4 sts=4 :

from subprocess import Popen, PIPE
from os import path

from pymin.seqtools import Sequence
from pymin.dispatcher import handler, HandlerError, Handler
from pymin.services.util import Restorable, ConfigWriter, InitdHandler, \
                                TransactionalHandler, call

__ALL__ = ('IpHandler', 'Error','DeviceError', 'DeviceNotFoundError',
           'RouteError', 'RouteNotFoundError', 'RouteAlreadyExistsError',
           'AddressError', 'AddressNotFoundError', 'AddressAlreadyExistsError')

class Error(HandlerError):
    r"""
    Error(command) -> Error instance :: Base IpHandler exception class.

    All exceptions raised by the IpHandler inherits from this one, so you can
    easily catch any IpHandler exception.

    message - A descriptive error message.
    """
    pass

class DeviceError(Error):

    def __init__(self, device):
        self.message = u'Device error : "%s"' % device

class DeviceNotFoundError(DeviceError):

    def __init__(self, device):
        self.message = u'Device not found : "%s"' % device

class AddressError(Error):

    def __init__(self, addr):
        self.message = u'Address error : "%s"' % addr

class AddressNotFoundError(AddressError):

    def __init__(self, address):
        self.message = u'Address not found : "%s"' % address

class AddressAlreadyExistsError(AddressError):

    def __init__(self, address):
        self.message = u'Address already exists : "%s"' % address

class RouteError(Error):

    def __init__(self, route):
        self.message = u'Route error : "%s"' % route

class RouteNotFoundError(RouteError):

    def __init__(self, route):
        self.message = u'Route not found : "%s"' % route

class RouteAlreadyExistsError(RouteError):

    def __init__(self, route):
        self.message = u'Route already exists : "%s"' % route


class Route(Sequence):

    def __init__(self, net_addr, prefix, gateway):
        self.net_addr = net_addr
        self.prefix = prefix
        self.gateway = gateway

    def as_tuple(self):
        return(self.addr, self.prefix, self.gateway)

    def __cmp__(self, other):
        if self.net_addr == other.net_addr \
                and self.prefix == other.prefix \
                and self.gateway == other.gateway:
            return 0
        return cmp(id(self), id(other))

class RouteHandler(Handler):

    handler_help = u"Manage IP routes"

    def __init__(self, parent):
        self.parent = parent

    @handler(u'Adds a route to a device')
    def add(self, device, net_addr, prefix, gateway):
        if not device in self.parent.devices:
            raise DeviceNotFoundError(device)
        r = Route(net_addr, prefix, gateway)
        try:
            self.parent.devices[device].routes.index(r)
            raise RouteAlreadyExistsError(net_addr + '/' + prefix + '->' + gateway)
        except ValueError:
            self.parent.devices[device].routes.append(r)

    @handler(u'Deletes a route from a device')
    def delete(self, device, net_addr, prefix, gateway):
        if not device in self.parent.devices:
            raise DeviceNotFoundError(device)
        r = Route(net_addr, prefix, gateway)
        try:
            self.parent.devices[device].routes.remove(r)
        except ValueError:
            raise RouteNotFoundError(net_addr + '/' + prefix + '->' + gateway)

    @handler(u'Flushes routes from a device')
    def flush(self, device):
        if not device in self.parent.devices:
            raise DeviceNotFoundError(device)
        self.parent.devices[device].routes = list()


    @handler(u'List routes')
    def list(self, device):
        try:
            k = self.parent.devices[device].routes.keys()
        except ValueError:
            k = list()
        return k

    @handler(u'Get information about all routes')
    def show(self):
        try:
            k = self.parent.devices[device].routes.values()
        except ValueError:
            k = list()
        return k


class Address(Sequence):

    def __init__(self, ip, prefix, broadcast):
        self.ip = ip
        self.prefix = prefix
        self.broadcast = broadcast

    def as_tuple(self):
        return (self.ip, self.prefix, self.broadcast)

class AddressHandler(Handler):

    handler_help = u"Manage IP addresses"

    def __init__(self, parent):
        self.parent = parent

    @handler(u'Adds an address to a device')
    def add(self, device, ip, prefix, broadcast='+'):
        if not device in self.parent.devices:
            raise DeviceNotFoundError(device)
        if ip in self.parent.devices[device].addrs:
            raise AddressAlreadyExistsError(ip)
        self.parent.devices[device].addrs[ip] = Address(ip, prefix, broadcast)

    @handler(u'Deletes an address from a device')
    def delete(self, device, ip):
        if not device in self.parent.devices:
            raise DeviceNotFoundError(device)
        if not ip in self.parent.devices[device].addrs:
            raise AddressNotFoundError(ip)
        del self.parent.devices[device].addrs[ip]

    @handler(u'Flushes addresses from a device')
    def flush(self, device):
        if not device in self.parent.devices:
            raise DeviceNotFoundError(device)
        self.parent.devices[device].addrs = dict()

    @handler(u'List all addresses from a device')
    def list(self, device):
        try:
            k = self.parent.devices[device].addrs.keys()
        except ValueError:
            k = list()
        return k

    @handler(u'Get information about addresses from a device')
    def show(self, device):
        try:
            k = self.parent.devices[device].addrs.values()
        except ValueError:
            k = list()
        return k


class Device(Sequence):

    def __init__(self, name, mac):
        self.name = name
        self.mac = mac
        self.addrs = dict()
        self.routes = list()

    def as_tuple(self):
        return (self.name, self.mac)

class DeviceHandler(Handler):

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
        if name in self.devices:
            call(self.device_template.render(dev=name, action='up'), shell=True)
        else:
            raise DeviceNotFoundError(name)

    @handler(u'Bring the device down')
    def down(self, name):
        if name in self.devices:
            call(self.device_template.render(dev=name, action='down'), shell=True)
        else:
            raise DeviceNotFoundError(name)

    @handler(u'List all devices')
    def list(self):
        return self.devices.keys()

    @handler(u'Get information about a device')
    def show(self):
        return self.devices.items()


def get_devices():
    p = Popen(('ip', 'link', 'list'), stdout=PIPE, close_fds=True)
    string = p.stdout.read()
    p.wait()
    d = dict()
    i = string.find('eth')
    while i != -1:
        eth = string[i:i+4]
        m = string.find('link/ether', i+4)
        mac = string[ m+11 : m+11+17]
        d[eth] = Device(eth, mac)
        i = string.find('eth', m+11+17)
    return d

class IpHandler(Restorable, ConfigWriter, TransactionalHandler):

    handler_help = u"Manage IP devices, addresses and routes"

    _persistent_attrs = 'devices'

    _restorable_defaults = dict(devices=get_devices())

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
                        prefix = address.prefix,
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
    ip.route.flush('eth0')
    ip.commit()
    ip.addr.delete('eth0','192.168.0.23')
    ip.commit()





# vim: set encoding=utf-8 et sw=4 sts=4 :

from mako.template import Template
from mako.runtime import Context
from subprocess import Popen, PIPE
from os import path
try:
    import cPickle as pickle
except ImportError:
    import pickle

try:
    from seqtools import Sequence
except ImportError:
    # NOP for testing
    class Sequence: pass
try:
    from dispatcher import handler, HandlerError
except ImportError:
    # NOP for testing
    class HandlerError(RuntimeError): pass
    def handler(f): return f

__ALL__ = ('IpHandler',)

pickle_ext = '.pkl'
pickle_devices = 'devs'

template_dir = path.join(path.dirname(__file__), 'templates')
command_filename = 'command'


device_com = 'device.command'
ip_add_com = 'ip_add.command'
ip_del_com = 'ip_del.command'
ip_flush_com = 'ip_flush.command'
route_add_com = 'route_add.command'
route_del_com = 'route_del.command'
route_flush_com = 'route_flush.command'

class Error(HandlerError):
    r"""
    Error(command) -> Error instance :: Base IpHandler exception class.

    All exceptions raised by the IpHandler inherits from this one, so you can
    easily catch any IpHandler exception.

    message - A descriptive error message.
    """

    def __init__(self, message):
        r"Initialize the Error object. See class documentation for more info."
        self.message = message

    def __str__(self):
        return self.message

class DeviceError(Error):

    def __init__(self, device):
        self.message = 'Device error : "%s"' % device

class DeviceNotFoundError(DeviceError):

    def __init__(self, device):
        self.message = 'Device not found : "%s"' % device

class AddressError(Error):

    def __init__(self, addr):
        self.message = 'Address error : "%s"' % addr

class AddressNotFoundError(AddressError):

    def __init__(self, address):
        self.message = 'Address not found : "%s"' % address

class AddressAlreadyExistsError(AddressError):

    def __init__(self, address):
        self.message = 'Address already exists : "%s"' % address

class RouteError(Error):

    def __init__(self, route):
        self.message = 'Route error : "%s"' % route

class RouteNotFoundError(RouteError):

    def __init__(self, route):
        self.message = 'Route not found : "%s"' % route

class RouteAlreadyExistsError(RouteError):

    def __init__(self, route):
        self.message = 'Route already exists : "%s"' % route

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

class RouteHandler:

    def __init__(self, devices):
        self.devices = devices

    @handler
    def add(self, device, net_addr, prefix, gateway):
        if not device in self.devices:
            raise DeviceNotFoundError(device)
        r = Route(net_addr, prefix, gateway)
        try:
            self.devices[device].routes.index(r)
            raise RouteAlreadyExistsError(net_addr + '/' + prefix + '->' + gateway)
        except ValueError:
            self.devices[device].routes.append(r)

    @handler
    def delete(self, device, net_addr, prefix, gateway):
        if not device in self.devices:
            raise DeviceNotFoundError(device)
        r = Route(net_addr, prefix, gateway)
        try:
            self.devices[device].routes.remove(r)
        except ValueError:
            raise RouteNotFoundError(net_addr + '/' + prefix + '->' + gateway)

    @handler
    def flush(self, device):
        if not device in self.devices:
            raise DeviceNotFoundError(device)
        self.devices[device].routes = list()


    @handler
    def list(self, device):
        try:
            k = self.devices[device].routes.keys()
        except ValueError:
            k = list()
        return k

    @handler
    def show(self):
        try:
            k = self.devices[device].routes.values()
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

class AddressHandler:

    def __init__(self, devices):
        self.devices = devices

    @handler
    def add(self, device, ip, prefix, broadcast='+'):
        if not device in self.devices:
            raise DeviceNotFoundError(device)
        if ip in self.devices[device].addrs:
            raise AddressAlreadyExistsError(ip)
        self.devices[device].addrs[ip] = Address(ip, prefix, broadcast)

    @handler
    def delete(self, device, ip):
        if not device in self.devices:
            raise DeviceNotFoundError(device)
        if not ip in self.devices[device].addrs:
            raise AddressNotFoundError(ip)
        del self.devices[device].addrs[ip]

    @handler
    def flush(self, device):
        if not device in self.devices:
            raise DeviceNotFoundError(device)
        self.devices[device].addrs = dict()

    @handler
    def list(self, device):
        try:
            k = self.devices[device].addrs.keys()
        except ValueError:
            k = list()
        return k

    @handler
    def show(self, device):
        try:
            k = self.devices[device].addrs.values()
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

class DeviceHandler:

    def __init__(self, devices):
        self.devices = devices
        dev_fn = path.join(template_dir, device_com)
        self.device_template = Template(filename=dev_fn)

    @handler
    def up(self, name):
        if name in self.devices:
            print self.device_template.render(dev=name, action='up')
        else:
            raise DeviceNotFoundError(name)

    @handler
    def down(self, name):
        if name in self.devices:
            print self.device_template.render(dev=name, action='down')
        else:
            raise DeviceNotFoundError(name)

    @handler
    def list(self):
        return self.devices.keys()

    @handler
    def show(self):
        return self.devices.items()

class IpHandler:

    def __init__(self, pickle_dir='.', config_dir='.'):
        r"Initialize DhcpHandler object, see class documentation for details."

        self.pickle_dir = pickle_dir
        self.config_dir = config_dir

        ip_add_fn = path.join(template_dir, ip_add_com)
        ip_del_fn = path.join(template_dir, ip_del_com)
        ip_flush_fn = path.join(template_dir, ip_flush_com)
        self.ip_add_template = Template(filename=ip_add_fn)
        self.ip_del_template = Template(filename=ip_del_fn)
        self.ip_flush_template = Template(filename=ip_flush_fn)

        route_add_fn = path.join(template_dir, route_add_com)
        route_del_fn = path.join(template_dir, route_del_com)
        route_flush_fn = path.join(template_dir, route_flush_com)
        self.route_add_template = Template(filename=route_add_fn)
        self.route_del_template = Template(filename=route_del_fn)
        self.route_flush_template = Template(filename=route_flush_fn)

        try:
            self._load()
        except IOError:
            p = Popen('ip link list', shell=True, stdout=PIPE, close_fds=True)
            devs = _get_devices(p.stdout.read())
            self.devices = dict()
            for eth, mac in devs.values():
                self.devices[eth] = Device(eth, mac)
            self._dump()
        self.addr = AddressHandler(self.devices)
        self.route = RouteHandler(self.devices)
        self.dev = DeviceHandler(self.devices)
        self.commit()

    @handler
    def commit(self):
        r"commit() -> None :: Commit the changes and reload the DHCP service."
        #esto seria para poner en una interfaz
        #y seria que hace el pickle deberia llamarse
        #al hacerse un commit
        self._dump()
        self._write_config()

    @handler
    def rollback(self):
        r"rollback() -> None :: Discard the changes not yet commited."
        self._load()

    def _dump(self):
        r"_dump() -> None :: Dump all persistent data to pickle files."
        # XXX podría ir en una clase base
        self._dump_var(self.devices, pickle_devices)


    def _load(self):
        r"_load() -> None :: Load all persistent data from pickle files."
        # XXX podría ir en una clase base
        self.devices = self._load_var(pickle_devices)

    def _pickle_filename(self, name):
        r"_pickle_filename() -> string :: Construct a pickle filename."
        # XXX podría ir en una clase base
        return path.join(self.pickle_dir, name) + pickle_ext

    def _dump_var(self, var, name):
        r"_dump_var() -> None :: Dump a especific variable to a pickle file."
        # XXX podría ir en una clase base
        pkl_file = file(self._pickle_filename(name), 'wb')
        pickle.dump(var, pkl_file, 2)
        pkl_file.close()

    def _load_var(self, name):
        r"_load_var()7 -> object :: Load a especific pickle file."
        # XXX podría ir en una clase base
        return pickle.load(file(self._pickle_filename(name)))

    def _write_config(self):
        r"_write_config() -> None :: Execute all commands."
        for device in self.devices.values():
            print self.route_flush_template.render(dev=device.name)
            print self.ip_flush_template.render(dev=device.name)
            for address in device.addrs.values():
                print self.ip_add_template.render(
                    dev=device.name,
                    addr=address.ip,
                    prefix=address.prefix,
                    broadcast=address.broadcast
                    )
            for route in device.routes:
                print self.route_add_template.render(
                    dev=device.name,
                    net_addr=route.net_addr,
                    prefix=route.prefix,
                    gateway=route.gateway
                    )

    def _get_devices(string):
       l = list()
       i = string.find('eth')
       while i != -1:
           eth = string[i:i+4]
           m = string.find('link/ether', i+4)
           mac = string[ m+11 : m+11+17]
           l.append((eth,mac))
           i = string.find('eth', m+11+17)
       return l

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





# vim: set encoding=utf-8 et sw=4 sts=4 :

from subprocess import Popen, PIPE
from os import path

from pymin.seqtools import Sequence
from pymin.dispatcher import handler, HandlerError, Handler
from pymin.services.util import Restorable, ConfigWriter, InitdHandler, \
                                TransactionalHandler, SubHandler, call, \
                                get_network_devices, ListComposedSubHandler, \
                                DictComposedSubHandler, Device, Address, ExecutionError

__ALL__ = ('IpHandler',)

# TODO: convertir HopHandler a ComposedSubHandler

class HopError(HandlerError):

    def __init__(self, hop):
        self.message = u'Hop error : "%s"' % hop

class HopNotFoundError(HopError):

    def __init__(self, hop):
        self.message = u'Hop not found : "%s"' % hop

class HopAlreadyExistsError(HopError):

    def __init__(self, hop):
        self.message = u'Hop already exists : "%s"' % hop


class Hop(Sequence):

    def __init__(self, gateway, device):
        self.gateway = gateway
        self.device = device

    def as_tuple(self):
        return (self.gateway, self.device)

    def __cmp__(self, other):
        if self.gateway == other.gateway \
                and self.device == other.device:
            return 0
        return cmp(id(self), id(other))

class HopHandler(Handler):

    def __init__(self, parent):
        self.parent = parent

    @handler('Adds a hop : add <gateway> <device>')
    def add(self, gw, dev):
        if not dev in self.parent.devices:
            raise DeviceNotFoundError(device)
        h = Hop(gw, dev)
        try:
            self.parent.hops.index(h)
            raise HopAlreadyExistsError(gw  + '->' + dev)
        except ValueError:
            self.parent.hops.append(h)

    @handler(u'Deletes a hop : delete <gateway> <device>')
    def delete(self, gw, dev):
        if not dev in self.parent.devices:
            raise DeviceNotFoundError(device)
        h = Hop(gw, dev)
        try:
            self.parent.hops.remove(h)
        except ValueError:
            raise HopNotFoundError(gw + '->' + dev)

    @handler(u'Lists hops : list <dev>')
    def list(self, device):
        try:
            k = self.parent.hops.keys()
        except ValueError:
            k = list()
        return k

    @handler(u'Get information about all hops: show <dev>')
    def show(self, device):
        try:
            k = self.parent.hops.values()
        except ValueError:
            k = list()
        return k

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


class AddressHandler(DictComposedSubHandler):
    handler_help = u"Manage IP addresses"
    _comp_subhandler_cont = 'devices'
    _comp_subhandler_attr = 'addrs'
    _comp_subhandler_class = Address


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
            #bring up all the route asocitaed to the device
            for route in self.parent.devices[name].routes:
                try:
                    call(self.parent._render_config('route_add', dict(
                            dev = name,
                            net_addr = route.net_addr,
                            prefix = route.prefix,
                            gateway = route.gateway,
                        )
                    ), shell=True)
                except ExecutionError, e:
                    print e
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

    handler_help = u"Manage IP devices, addresses, routes and hops"

    _persistent_attrs = ('devices','hops')

    _restorable_defaults = dict(
                            devices=get_network_devices(),
                            hops = list()
                            )

    _config_writer_files = ('device', 'ip_add', 'ip_del', 'ip_flush',
                            'route_add', 'route_del', 'route_flush', 'hop')
    _config_writer_tpl_dir = path.join(path.dirname(__file__), 'templates')

    def __init__(self, pickle_dir='.', config_dir='.'):
        r"Initialize DhcpHandler object, see class documentation for details."
        self._persistent_dir = pickle_dir
        self._config_writer_cfg_dir = config_dir
        self._config_build_templates()
        self._restore()
        self._write_config()
        self.addr = AddressHandler(self)
        self.route = RouteHandler(self)
        self.dev = DeviceHandler(self)
        self.hop = HopHandler(self)
        self.services = list()

    def _write_config(self):
        r"_write_config() -> None :: Execute all commands."
        for device in self.devices.values():
            if device.active:
                self._write_config_for_device(device)
        self._write_hops()

    def _write_hops(self):
        r"_write_hops() -> None :: Execute all hops."
        if self.hops:
            try:
                call('ip route del default', shell=True)
            except ExecutionError, e:
                print e
            try:
                #get hops for active devices
                active_hops = dict()
                for h in self.hops:
                    if h.device in self.devices:
                        if self.devices[h.device].active:
                            active_hops.append(h)
                call(self._render_config('hop', dict(
                    hops = active_hops,
                        )
                ), shell=True)
            except ExecutionError, e:
                print e

    def _write_config_for_device(self, device):
        r"_write_config_for_device(self, device) -> None :: Execute all commands for a device."
        try:
            call(self._render_config('route_flush', dict(dev=device.name)), shell=True)
        except ExecutionError, e:
            print e
        try:
            call(self._render_config('ip_flush', dict(dev=device.name)), shell=True)
        except ExecutionError, e:
            print e
        for address in device.addrs.values():
            broadcast = address.broadcast
            if broadcast is None:
                broadcast = '+'
            try:
                call(self._render_config('ip_add', dict(
                    dev = device.name,
                    addr = address.ip,
                    netmask = address.netmask,
                    peer = address.peer,
                    broadcast = broadcast,
                    )
                ), shell=True)
            except ExecutionError, e:
                print e
        for route in device.routes:
            try:
                call(self._render_config('route_add', dict(
                        dev = device.name,
                        net_addr = route.net_addr,
                        prefix = route.prefix,
                        gateway = route.gateway,
                    )
                ), shell=True)
            except ExecutionError, e:
                print e

    def handle_timer(self):
        self.refresh_devices()


    def refresh_devices(self):
        devices = get_network_devices()
        #add not registered and active devices
        go_active = False
        for k,v in devices.items():
            if k not in self.devices:
                self.devices[k] = v
            elif not self.devices[k].active:
                self.active = True
                go_active = True
                self._write_config_for_device(self.devices[k])
        if go_active:
            self._write_hops()
            for s in services:
                if s._running:
                    try:
                        s.stop()
                    except ExecutionError:
                        pass
                    try:
                        s.start()
                    except ExecutionError:
                        pass

        #mark inactive devices
        for k in self.devices.keys():
            if k not in devices:
                self.devices[k].active = False

	#hooks a service to the ip handler, so when
	#a device is brought up one can restart the service
	#that need to refresh their device list
	def device_up_hook(self, serv):
		if hasattr(serv, 'stop') and hasattr(serv, 'start'):
			services.append(serv)





if __name__ == '__main__':

    ip = IpHanlder()
    print '----------------------'
    ip.hop.add('201.21.32.53','eth0')
    ip.hop.add('205.65.65.25','eth1')
    ip.commit()
    ip.dev.up('eth0')
    ip.addr.add('eth0','192.168.0.23','24','192.168.255.255')
    ip.addr.add('eth0','192.168.0.26','24')
    ip.commit()
    ip.route.add('eth0','192.168.0.0','24','192.168.0.1')
    ip.route.add('eth0','192.168.0.5','24','192.168.0.1')
    ip.commit()
    ip.hop.delete('201.21.32.53','eth0')
    ip.route.clear('eth0')
    ip.commit()




# vim: set encoding=utf-8 et sw=4 sts=4 :

from os import path
import logging ; log = logging.getLogger('pymin.services.ip')

from pymin.service.util import Restorable, ConfigWriter, call, \
                               TransactionalHandler, ExecutionError, \
                               get_network_devices

from hop import HopHandler
from route import RouteHandler
from addr import AddressHandler
from dev import DeviceHandler

__all__ = ('IpHandler',)


class IpHandler(Restorable, ConfigWriter, TransactionalHandler):

    handler_help = u"Manage IP devices, addresses, routes and hops"

    _persistent_attrs = ('devices','hops','no_device_routes')

    _restorable_defaults = dict(
                            devices=get_network_devices(),
                            hops = list(),
                            no_device_routes = list(),
                            )

    _config_writer_files = ('device', 'ip_add', 'ip_del', 'ip_flush',
                            'route_add', 'route_del', 'route_flush', 'hop')
    _config_writer_tpl_dir = path.join(path.dirname(__file__), 'templates')

    def __init__(self, pickle_dir='.', config_dir='.'):
        r"Initialize DhcpHandler object, see class documentation for details."
        log.debug(u'IpHandler(%r, %r)', pickle_dir, config_dir)
        self._persistent_dir = pickle_dir
        self._config_writer_cfg_dir = config_dir
        self._config_build_templates()
        self._restore()
        self._write_config()
        self.addr = AddressHandler(self)
        self.route = RouteHandler(self)
        self.dev = DeviceHandler(self)
        self.hop = HopHandler(self)
        self.no_device_routes = list()
        self.services = list()

    def _write_config(self):
        r"_write_config() -> None :: Execute all commands."
        log.debug(u'IpHandler._write_config()')
        for device in self.devices.values():
            log.debug(u'IpHandler._write_config: processing device %s', device)
            if device.active:
                self._write_config_for_device(device)
        self._bring_up_no_dev_routes()
        self._write_hops()

    def _bring_up_no_dev_routes(self):
        log.debug(u'IpHandler._bring_up_no_dev_routes()')
        for route in self.no_device_routes:
            try:
                log.debug(u'IpHandler._bring_up_no_dev_routes: add %r', route)
                call(self._render_config('route_add', dict(
                        dev = None,
                        net_addr = route.net_addr,
                        prefix = route.prefix,
                        gateway = route.gateway,
                    )
                ), shell=True)
            except ExecutionError, e:
                log.debug(u'IpHandler._write_config: error flushing -> %r', e)

    def _write_hops(self):
        r"_write_hops() -> None :: Execute all hops."
        log.debug(u'IpHandler._write_hops()')
        if self.hops:
            log.debug(u'IpHandler._write_hops: we have hops: %r', self.hops)
            try:
                log.debug(u'IpHandler._write_hops: flushing default hops')
                call('ip route del default', shell=True)
            except ExecutionError, e:
                log.debug(u'IpHandler._write_hops: error adding -> %r', e)
            try:
                log.debug(u'IpHandler._write_hops: configuring hops')
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
                log.debug(u'IpHandler._write_hops: error adding -> %r', e)

    def _write_config_for_device(self, device):
        r"_write_config_for_device(self, device) -> None :: Execute commands."
        log.debug(u'IpHandler._write_config_for_device()')
        try:
            log.debug(u'IpHandler._write_config_for_device: flushing routes...')
            call(self._render_config('route_flush', dict(dev=device.name)),
                        shell=True)
        except ExecutionError, e:
            log.debug(u'IpHandler._write_config_for_device: error flushing '
                        u'-> %r', e)
        try:
            log.debug(u'IpHandler._write_config_for_device: flushing addrs...')
            call(self._render_config('ip_flush', dict(dev=device.name)),
                        shell=True)
        except ExecutionError, e:
            log.debug(u'IpHandler._write_config_for_device: error flushing '
                        u'-> %r', e)
        for address in device.addrs.values():
            broadcast = address.broadcast
            if broadcast is None:
                broadcast = '+'
            try:
                log.debug(u'IpHandler._write_config_for_device: adding %r',
                            address)
                call(self._render_config('ip_add', dict(
                    dev = device.name,
                    addr = address.ip,
                    netmask = address.netmask,
                    peer = address.peer,
                    broadcast = broadcast,
                    )
                ), shell=True)
            except ExecutionError, e:
                log.debug(u'IpHandler._write_config_for_device: error adding '
                            u'-> %r', e)
        for route in device.routes:
            try:
                log.debug(u'IpHandler._write_config_for_device: adding %r',
                            route)
                call(self._render_config('route_add', dict(
                        dev = device.name,
                        net_addr = route.net_addr,
                        prefix = route.prefix,
                        gateway = route.gateway,
                    )
                ), shell=True)
            except ExecutionError, e:
                log.debug(u'IpHandler._write_config_for_device: error adding '
                            u'-> %r', e)

    def handle_timer(self):
        log.debug(u'IpHandler.handle_timer()')
        self.refresh_devices()

    def refresh_devices(self):
        log.debug(u'IpHandler.update_devices()')
        devices = get_network_devices()
        #add not registered and active devices
        go_active = False
        for k,v in devices.items():
            if k not in self.devices:
                log.debug(u'IpHandler.update_devices: adding %r', v)
                self.devices[k] = v
            elif not self.devices[k].active:
                self.active = True
                go_active = True
                self._write_config_for_device(self.devices[k])
        if go_active:
            self._write_hops()
            self._bring_up_no_dev_routes()
            self._restart_services()

        #mark inactive devices
        for k in self.devices.keys():
            go_down = False
            if k not in devices:
                log.debug(u'IpHandler.update_devices: removing %s', k)
                self.devices[k].active = False
                go_down = True
            if go_down:
                self._bring_up_no_dev_routes()

    def _restart_services(self):
        for s in self.services:
            if s._service_running:
                try:
                     s.stop()
                except ExecutionError:
                    pass
                try:
                    s.start()
                except ExecutionError:
                    pass

	#hooks a service to the ip handler, so when
	#a device is brought up one can restart the service
	#that need to refresh their device list
    def device_up_hook(self, serv):
        if hasattr(serv, 'stop') and hasattr(serv, 'start'):
            self.services.append(serv)





if __name__ == '__main__':

    logging.basicConfig(
        level   = logging.DEBUG,
        format  = '%(asctime)s %(levelname)-8s %(message)s',
        datefmt = '%H:%M:%S',
    )

    ip = IpHandler()
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




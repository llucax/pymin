# vim: set encoding=utf-8 et sw=4 sts=4 :

from os import path
import logging ; log = logging.getLogger('pymin.services.ip')

from pymin.dispatcher import handler
from pymin.service.util import SubHandler, call, ContainerNotFoundError, \
                               ExecutionError

__all__ = ('DeviceHandler',)


class DeviceHandler(SubHandler):

    handler_help = u"Manage network devices"

    def __init__(self, parent):
        log.debug(u'DeviceHandler(%r)', parent)
        # FIXME remove templates to execute commands
        from mako.template import Template
        self.parent = parent
        template_dir = path.join(path.dirname(__file__), 'templates')
        dev_fn = path.join(template_dir, 'device')
        self.device_template = Template(filename=dev_fn)

    @handler(u'Bring the device up')
    def up(self, name):
        log.debug(u'DeviceHandler.up(%r)', name)
        if name in self.parent.devices:
            call(self.device_template.render(dev=name, action='up'), shell=True)
            #bring up all the route asocitaed to the device
            for route in self.parent.devices[name].routes:
                try:
                    log.debug(u'IpHandler.up: adding %r', route)
                    call(self.parent._render_config('route_add', dict(
                            dev = name,
                            net_addr = route.net_addr,
                            prefix = route.prefix,
                            gateway = route.gateway,
                        )
                    ), shell=True)
                except ExecutionError, e:
                    log.debug(u'IpHandler.up: error adding %r -> %r', route, e)
            self.parent._bring_up_no_dev_routes()
            self.parent._restart_services()
        else:
            log.debug(u'DeviceHandler.up: device not found')
            raise ContainerNotFoundError(name)

    @handler(u'Bring the device down')
    def down(self, name):
        log.debug(u'DeviceHandler.down(%r)', name)
        if name in self.parent.devices:
            call(self.device_template.render(dev=name, action='down'), shell=True)
            self.parent._bring_up_no_dev_routes()
            self.parent._restart_services()
        else:
            log.debug(u'DeviceHandler.up: device not found')
            raise ContainerNotFoundError(name)

    @handler(u'List all devices')
    def list(self):
        log.debug(u'DeviceHandler.list()')
        return self.parent.devices.keys()

    @handler(u'Get information about a device')
    def show(self):
        log.debug(u'DeviceHandler.show()')
        return self.parent.devices.items()


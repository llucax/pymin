# vim: set encoding=utf-8 et sw=4 sts=4 :

from os import path

from pymin.seqtools import Sequence
from pymin.dispatcher import handler
from pymin.service.util import SubHandler, ExecutionError, ItemNotFoundError, \
                               call

__all__ = ('DeviceHandler',)


class Device(Sequence):

    def __init__(self, name, mac):
        self.name = name
        self.mac = mac
        self.classes = dict()

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
            try:
                call(self.device_template.render(dev=name, action='add'), shell=True)
            except ExecutionError:
                pass
        else:
            raise ItemNotFoundError(name)

    @handler(u'Bring the device down')
    def down(self, name):
        if name in self.parent.devices:
            try:
                call(self.device_template.render(dev=name, action='del'), shell=True)
            except ExecutionError:
                pass
        else:
            raise ItemNotFoundError(name)

    @handler(u'List all devices')
    def list(self):
        return self.parent.devices.keys()

    @handler(u'Get information about a device')
    def show(self):
        return self.parent.devices.items()


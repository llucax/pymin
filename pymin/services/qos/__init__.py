# vim: set encoding=utf-8 et sw=4 sts=4 :

from subprocess import Popen, PIPE
from os import path

from pymin.seqtools import Sequence
from pymin.dispatcher import handler, HandlerError, Handler
from pymin.services.util import Restorable, ConfigWriter, InitdHandler, \
                                TransactionalHandler, SubHandler, call, \
                                get_network_devices, ListComposedSubHandler, \
                                DictComposedSubHandler

__ALL__ = ('QoSHandler',)

class ClassError(HandlerError):

    def __init__(self, qosclass):
        self.message = u'Class error : "%s"' % qosclass


class ClassNotFoundError(ClassError):

    def __init__(self, qosclass):
        self.message = u'Class not found : "%s"' % qosclass


class ClassAlreadyExistsError(ClassError):

    def __init__(self, qosclass):
        self.message = u'Class already exists : "%s"' % qosclass


class Class(Sequence):

    def __init__(self, id, rate=None):
        self.id = id
        self.rate = rate
        self.hosts = list()

    def as_tuple(self):
        return (self.id, self.rate)

    def __cmp__(self, other):
        if self.id == other.id
            return 0
        return cmp(id(self), id(other))


class ClassHandler(Handler):

    def __init__(self, parent):
        self.parent = parent

    @handler('Adds a class : add <id> <device> <rate>')
    def add(self, id, dev, rate):
        if not dev in self.parent.devices:
            raise DeviceNotFoundError(device)
        c = Class(id, dev, rate)
        try:
            self.parent.classes.index(c)
            raise ClassAlreadyExistsError(id  + '->' + dev)
        except ValueError:
            self.parent.classes.append(c)

    @handler(u'Deletes a class : delete <id> <device>')
    def delete(self, id, dev):
        if not dev in self.parent.devices:
            raise DeviceNotFoundError(device)
        c = Class(id, dev)
        try:
            self.parent.classes.remove(c)
        except ValueError:
            raise ClassNotFoundError(id + '->' + dev)

    @handler(u'Lists classes : list <dev>')
    def list(self, device):
        try:
            k = self.parent.classes.keys()
        except ValueError:
            k = list()
        return k

    @handler(u'Get information about all classes: show <dev>')
    def show(self, device):
        try:
            k = self.parent.classes.values()
        except ValueError:
            k = list()
        return k


class Host(Sequence):

    def __init__(self, ip):
        self.ip = ip

    def as_tuple(self):
        return (self.ip)


class HostHandler(DictComposedSubHandler):
    handler_help = u"Manage Hosts"
    _comp_subhandler_cont = 'classes'
    _comp_subhandler_attr = 'hosts'
    _comp_subhandler_class = Host


class Device(Sequence):

    def __init__(self, name, mac):
        self.name = name
        self.mac = mac
        self.classes = list()

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
            call(self.device_template.render(dev=name, action='add'), shell=True)
        else:
            raise DeviceNotFoundError(name)

    @handler(u'Bring the device down')
    def down(self, name):
        if name in self.parent.devices:
            call(self.device_template.render(dev=name, action='del'), shell=True)
        else:
            raise DeviceNotFoundError(name)

    @handler(u'List all devices')
    def list(self):
        return self.parent.devices.keys()

    @handler(u'Get information about a device')
    def show(self):
        return self.parent.devices.items()


class QoSHandler(Restorable, ConfigWriter, TransactionalHandler):

    handler_help = u"Manage QoS devices, classes and hosts"

    _persistent_attrs = ('devices','classes','hosts')

    _restorable_defaults = dict(
                            devices=dict((dev, Device(dev, mac))
                                for (dev, mac) in get_network_devices().items()),
                            classes = list()
                            hosts = list()
                            )

    _config_writer_files = ('device', 'class_add', 'class_del', 'host_add')

    _config_writer_tpl_dir = path.join(path.dirname(__file__), 'templates')

    def __init__(self, pickle_dir='.', config_dir='.'):
        r"Initialize QoSHandler object, see class documentation for details."
        self._persistent_dir = pickle_dir
        self._config_writer_cfg_dir = config_dir
        self._config_build_templates()
        self._restore()
        self._write_config()
        self.dev = DeviceHandler(self)
        self.classes = ClassHandler(self)
        self.hosts = HostHandler(self)

    def _write_config(self):
        r"_write_config() -> None :: Execute all commands."
        for device in self.devices.values():
            call(self._render_config('devices', dict(dev=device.name, action='del')), shell=True)
            call(self._render_config('devices', dict(dev=device.name, action='add')), shell=True)
            for qosclass in device.classes:
                call(self._render_config('class_add', dict(
                        dev = device.name,
                        id = qosclass.id,
                        rate = qosclass.rate
                    )
                ), shell=True)
            for host in classes.hosts:
                call(self._render_config('host_add', dict(
                        dev = device.name,
                        ip = host.ip,
                        id = qosclass.id
                    )
                ), shell=True)

    def handle_timer(self):
        self.refresh_devices()

    def refresh_devices(self):
        devices = get_network_devices()
        #add not registered devices
        for k, v in devices.items():
            if k not in self.devices:
                self.devices[k] = Device(k, v)
        #delete dead devices
        for k in self.devices.keys():
            if k not in devices:
                del self.devices[k]


if __name__ == '__main__':

    qos = QoSHandler()
    print '----------------------'
    qos.commit()

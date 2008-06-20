# vim: set encoding=utf-8 et sw=4 sts=4 :

from os import path

from pymin.seqtools import Sequence
from pymin.dispatcher import handler
from pymin.service.util import Restorable, ConfigWriter, \
                               TransactionalHandler, SubHandler, call, \
                               get_network_devices, ExecutionError, \
                               ContainerNotFoundError, ItemNotFoundError, \
                               ItemAlreadyExistsError

__all__ = ('QoSHandler')


class Class(Sequence):

    def __init__(self, cid, rate=None):
        self.cid = cid
        self.rate = rate
        self.hosts = dict()

    def as_tuple(self):
        return (self.cid, self.rate)

    def __cmp__(self, other):
        if self.cid == other.cid:
            return 0
        return cmp(id(self), id(other))


class ClassHandler(SubHandler):

    def __init__(self, parent):
        self.parent = parent

    @handler('Adds a class : add <id> <device> <rate>')
    def add(self, dev, cid, rate):
        if not dev in self.parent.devices:
            raise ContainerNotFoundError(dev)

        try:
            self.parent.devices[dev].classes[cid] = Class(cid, rate)
        except ValueError:
            raise ItemAlreadyExistsError(cid  + ' -> ' + dev)

    @handler(u'Deletes a class : delete <id> <device>')
    def delete(self, dev, cid):
        if not dev in self.parent.devices:
            raise ContainerNotFoundError(dev)

        try:
            del self.parent.devices[dev].classes[cid]
        except KeyError:
            raise ItemNotFoundError(cid + ' -> ' + dev)

    @handler(u'Lists classes : list <dev>')
    def list(self, dev):
        try:
            k = self.parent.devices[dev].classes.items()
        except KeyError:
            k = dict()
        return k


class Host(Sequence):

    def __init__(self, ip):
        self.ip = ip

    def as_tuple(self):
        return (self.ip)

    def __cmp__(self, other):
        if self.ip == other.ip:
            return 0
        return cmp(id(self), id(other))


class HostHandler(SubHandler):

    def __init__(self, parent):
        self.parent = parent

    @handler('Adds a host to a class : add <device> <class id> <ip>')
    def add(self, dev, cid, ip):
        if not dev in self.parent.devices:
            raise ContainerNotFoundError(dev)

        if not cid in self.parent.devices[dev].classes:
            raise ContainerNotFoundError(cid)

        try:
            self.parent.devices[dev].classes[cid].hosts[ip] = Host(ip)
        except ValueError:
            raise ItemAlreadyExistsError(h  + ' -> ' + dev)

    @handler(u'Lists hosts : list <dev> <class id>')
    def list(self, dev, cid):
        try:
            k = self.parent.devices[dev].classes[cid].hosts.keys()
        except KeyError:
            k = dict()
        return k


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


class QoSHandler(Restorable, ConfigWriter, TransactionalHandler):

    handler_help = u"Manage QoS devices, classes and hosts"

    _persistent_attrs = ('devices')

    _restorable_defaults = dict(
                            devices=dict((dev, Device(dev, mac))
                                for (dev, mac) in get_network_devices().items())
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
        self.cls = ClassHandler(self)
        self.host = HostHandler(self)

    def _write_config(self):
        r"_write_config() -> None :: Execute all commands."
        for device in self.devices.values():
            try:
                call(self._render_config('device', dict(dev=device.name, action='del')), shell=True)
            except ExecutionError:
                pass

            try:
                call(self._render_config('device', dict(dev=device.name, action='add')), shell=True)
            except ExecutionError:
                pass

            for cls in device.classes.values():
                try:
                    call(self._render_config('class_add', dict(
                        dev = device.name,
                        cid = cls.cid,
                        rate = cls.rate
                        )
                    ), shell=True)
                except ExecutionError:
                    pass

                for host in cls.hosts.values():
                    try:
                        call(self._render_config('host_add', dict(
                            dev = device.name,
                            ip = host.ip,
                            cid = cls.cid
                            )
                        ), shell=True)
                    except ExecutionError:
                        pass

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

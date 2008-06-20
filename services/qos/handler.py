# vim: set encoding=utf-8 et sw=4 sts=4 :

from os import path

from pymin.service.util import Restorable, ConfigWriter, \
                               TransactionalHandler, ExecutionError, \
                               call, get_network_devices

from cls import ClassHandler
from dev import DeviceHandler, Device
from host import HostHandler

__all__ = ('QoSHandler',)


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


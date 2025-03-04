# vim: set encoding=utf-8 et sw=4 sts=4 :

from os import path
import logging ; log = logging.getLogger('pymin.services.proxy')

from pymin.service.util import Restorable, ConfigWriter, InitdHandler, \
                               TransactionalHandler, ParametersHandler

from host import HostHandler
from user import UserHandler

__all__ = ('ProxyHandler',)


class ProxyHandler(Restorable, ConfigWriter, InitdHandler,
                   TransactionalHandler, ParametersHandler):

    handler_help = u"Manage proxy service"

    _initd_name = 'squid'

    _persistent_attrs = ('params', 'hosts', 'users')

    _restorable_defaults = dict(
            hosts = dict(),
            params  = dict(
                ip   = '192.168.0.1',
                port = '8080',
            ),
            users = dict(),
    )

    _config_writer_files = ('squid.conf','users.conf')
    _config_writer_tpl_dir = path.join(path.dirname(__file__), 'templates')

    def __init__(self, pickle_dir='.', config_dir='.'):
        r"Initialize DhcpHandler object, see class documentation for details."
        log.debug(u'ProxyHandler(%r, %r)', pickle_dir, config_dir)
        self._persistent_dir = pickle_dir
        self._config_writer_cfg_dir = config_dir
        self._config_build_templates()
        InitdHandler.__init__(self)
        self.host = HostHandler(self)
        self.user = UserHandler(self)

    def _get_config_vars(self, config_file):
        if config_file == 'squid.conf':
            return dict(hosts=self.hosts.values(), **self.params)
        return dict(users=self.users)


if __name__ == '__main__':

    logging.basicConfig(
        level   = logging.DEBUG,
        format  = '%(asctime)s %(levelname)-8s %(message)s',
        datefmt = '%H:%M:%S',
    )

    px = ProxyHandler()
    px.set('ip','192.66.66.66')
    px.set('port','666')
    px.host.add('192.168.0.25.25')
    px.host.add('192.168.0.25.26')
    px.host.add('192.168.0.25.27')
    px.host.delete('192.168.0.25.27')
    px.user.add('lala','soronga')
    px.user.add('culo','sarasa')
    px.commit()

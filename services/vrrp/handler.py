# vim: set encoding=utf-8 et sw=4 sts=4 :

import logging ; log = logging.getLogger('pymin.services.vrrp')

from pymin import procman
from pymin.service.util import Restorable, TransactionalHandler, \
                               ReloadHandler, RestartHandler, \
                               ServiceHandler, ParametersHandler

__all__ = ('VrrpHandler', 'get_service')


def get_service(config):
    return VrrpHandler(config.vrrp.pickle_dir, config.vrrp.config_dir)


# FIXME the the command should not use new parameters unless commit where called
#       i.e. integrate commit with procman to update internal procman parameters.
class VrrpHandler(Restorable, ParametersHandler, ReloadHandler, RestartHandler,
                        ServiceHandler, TransactionalHandler):

    handler_help = u"Manage VRRP service"

    _persistent_attrs = ['params']

    _restorable_defaults = dict(
        params = dict(
                ipaddress = '192.168.0.1',
                id        = '1',
                prio      = '',
                dev       = 'eth0',
                persist   = True,
            ),
        )

    @property
    def _command(self):
        command = ['vrrpd', '-i', self.params['dev'], '-v', self.params['id']]
        if self.params['prio']:
            command.extend(('-p', self.params['prio']))
        command.append(self.params['ipaddress'])
        return command

    def _service_start(self):
        log.debug(u'VrrpHandler._service_start()')
        procinfo = procman.get('vrrp')
        procinfo.command = self._command
        procinfo.persist = self.params['persist']
        procman.start('vrrp')

    def _service_stop(self):
        log.debug(u'VrrpHandler._service_stop()')
        procman.stop('vrrp')

    def _service_restart(self):
        procinfo = procman.get('vrrp')
        procinfo.command = self._command
        procinfo.persist = self.params['persist']
        procman.restart('vrrp')

    def __init__(self, pickle_dir='.', config_dir='.', pid_dir='.'):
        log.debug(u'VrrpHandler(%r, %r, %r)', pickle_dir, config_dir, pid_dir)
        self._persistent_dir = pickle_dir
        self._pid_dir = pid_dir
        procman.register('vrrp', None)
        ServiceHandler.__init__(self)


if __name__ == '__main__':

    logging.basicConfig(
        level   = logging.DEBUG,
        format  = '%(asctime)s %(levelname)-8s %(message)s',
        datefmt = '%H:%M:%S',
    )

    v = VrrpHandler()
    v.set('prio', '10')
    v.commit()


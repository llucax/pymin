# vim: set encoding=utf-8 et sw=4 sts=4 :

import os
from os import path
from signal import SIGTERM
from subprocess import Popen, PIPE

from pymin import procman
from pymin.seqtools import Sequence
from pymin.dispatcher import Handler, handler, HandlerError
from pymin.services.util import Restorable, TransactionalHandler, \
                                ReloadHandler, RestartHandler, \
                                ServiceHandler, ParametersHandler, call

__ALL__ = ('VrrpHandler',)

# FIXME the the command should not use new parameters unless commit where called
#       i.e. integrate commit with procman to update internal procman parameters.
class VrrpHandler(Restorable, ParametersHandler, ReloadHandler, RestartHandler,
                        ServiceHandler, TransactionalHandler):

    handler_help = u"Manage VRRP service"

    _persistent_attrs = ['params']

    _restorable_defaults = dict(
        params = dict(
                ipaddress='192.168.0.1',
                id = '1',
                prio = '',
                dev = 'eth0',
                persist = True,
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
        procinfo = procman.get('vrrp')
        procinfo.command = self._command
        procinfo.persist = self.params['persist']
        procman.start('vrrp')

    def _service_stop(self):
        procman.stop('vrrp')

    def _service_restart(self):
        procinfo = procman.get('vrrp')
        procinfo.command = self._command
        procinfo.persist = self.params['persist']
        procman.restart('vrrp')

    def __init__(self, pickle_dir='.', config_dir='.', pid_dir='.'):
        self._persistent_dir = pickle_dir
        self._pid_dir = pid_dir
        procman.register('vrrp', None)
        ServiceHandler.__init__(self)


if __name__ == '__main__':
    v = VrrpHandler()
    v.set('prio','10')
    v.commit()


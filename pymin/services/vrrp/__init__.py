# vim: set encoding=utf-8 et sw=4 sts=4 :

import os
from os import path
from signal import SIGTERM
from subprocess import Popen, PIPE

from pymin.seqtools import Sequence
from pymin.dispatcher import Handler, handler, HandlerError
from pymin.services.util import Restorable, TransactionalHandler, \
                                ReloadHandler, RestartHandler, \
                                ServiceHandler, ParametersHandler, call

__ALL__ = ('VrrpHandler',)

pid_filename = 'vrrp.pid'

class VrrpHandler(Restorable, ParametersHandler, ReloadHandler, RestartHandler,
                        ServiceHandler, TransactionalHandler):

    handler_help = u"Manage VRRP service"

    _persistent_attrs = ['params']

    _restorable_defaults = dict(
                            params = dict( ipaddress='192.168.0.1',
                                            id = '1',
                                            prio = '',
                                            dev = 'eth0',
                                    ),
                            )

    def _service_start(self):
        if self.params['prio'] != '':
            call(('vrrp', '-i', self.params['dev'], '-v', self.params['id'],
                    '-p', self.params['prio'], self.params['ipaddress']))
        else:
            call(('vrrp', '-i', self.params['dev'], '-v', self.params['id'], \
                    self.params['ipaddress']))

    def _service_stop(self):
        try:
            pid = file(path.join(self._pid_dir, pid_filename )).read().strip()
            os.kill(int(pid), SIGTERM)
        except (IOError, OSError):
            # TODO log
            pass

    def __init__(self, pickle_dir='.', config_dir='.', pid_dir='.'):
        self._persistent_dir = pickle_dir
        self._pid_dir = pid_dir
        ServiceHandler.__init__(self)


if __name__ == '__main__':
    v = VrrpHandler()
    v.set('prio','10')
    v.commit()
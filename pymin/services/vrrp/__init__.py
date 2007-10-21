# vim: set encoding=utf-8 et sw=4 sts=4 :

from os import path
from subprocess import Popen, PIPE

from pymin.seqtools import Sequence
from pymin.dispatcher import Handler, handler, HandlerError
from pymin.services.util import Restorable, TransactionalHandler, ParametersHandler, call

__ALL__ = ('VrrpHandler',)

class VrrpHandler(Restorable, ParametersHandler, TransactionalHandler):
    handler_help = u"Manage VRRP service"

    _persistent_attrs = 'params'

    _restorable_defaults = dict(
                            params = dict( ipaddress='192.168.0.1',
                                            id = '1',
                                            prio = '',
                                            dev = 'eth0',
                                    ),
                            )

    def __init__(self, pickle_dir='.', config_dir='.', pid_dir='.'):
        self._persistent_dir = pickle_dir
        self._pid_dir = pid_dir
        self._restore()

    @handler('Starts the service')
    def start(self):
        if self.params['prio'] != '':
            call(('/usr/local/bin/vrrpd','-i',self.params['dev'],'-v',self.params['id'],'-p',self.params['prio'],self.params['ipaddress']))
            #print ('vrrpd','-i',self.params['dev'],'-v',self.params['id'],'-p',self.params['prio'],self.params['ipaddress'])
        else:
            call(('/usr/local/bin/vrrpd','-i',self.params['dev'],'-v',self.params['id'],self.params['ipaddress']))
            #print ('vrrpd','-i',self.params['dev'],'-v',self.params['id'],self.params['ipaddress'])

    @handler('Stop the service')
    def stop(self):
        try :
            pid = 'vrrpd' + '_' + self.params['dev'] + '_' + self.params['id'] + '.pid'
            f = file(path.join(self._pid_dir, pid ), 'r')
            call(('kill',f.read().strip('\n')))
            #print('kill','<',f.read())
        except IOError:
            pass

    @handler('Reloads the service')
    def reload(self):
        self.stop()
        self.start()


if __name__ == '__main__':
    v = VrrpHandler()
    v.set('prio','10')
    v.commit()

# vim: set encoding=utf-8 et sw=4 sts=4 :

import logging ; log = logging.getLogger('pymin.services.nat')

from pymin.service.util import Restorable, ConfigWriter, ReloadHandler, \
                               ServiceHandler, TransactionalHandler, call

from portfw import PortForwardHandler
from snat import SNatHandler
from masq import MasqHandler

__all__ = ('NatHandler',)


class NatHandler(Restorable, ConfigWriter, ReloadHandler, ServiceHandler,
                        TransactionalHandler):
    r"""NatHandler([pickle_dir[, config_dir]]) -> NatHandler instance.

    Handles NAT commands using iptables.

    pickle_dir - Directory where to write the persistent configuration data.

    config_dir - Directory where to store de generated configuration files.

    Both defaults to the current working directory.
    """

    handler_help = u"Manage NAT (Network Address Translation) service."

    _persistent_attrs = ('ports', 'snats', 'masqs')

    _restorable_defaults = dict(
        ports=list(),
        snats=list(),
        masqs=list(),
    )

    def _service_start(self):
        log.debug(u'NatHandler._service_start(): flushing nat table')
        call(('iptables', '-t', 'nat', '-F'))
        for (index, port) in enumerate(self.ports):
            log.debug(u'NatHandler._service_start: adding port %r', port)
            call(['iptables'] + port.as_call_list(index+1))
        for (index, snat) in enumerate(self.snats):
            log.debug(u'NatHandler._service_start: adding snat %r', snat)
            call(['iptables'] + snat.as_call_list(index+1))
        for (index, masq) in enumerate(self.masqs):
            log.debug(u'NatHandler._service_start: adding masq %r', masq)
            call(['iptables'] + masq.as_call_list(index+1))

    def _service_stop(self):
        log.debug(u'NatHandler._service_stop(): flushing nat table')
        call(('iptables', '-t', 'nat', '-F'))

    _service_restart = _service_start

    def __init__(self, pickle_dir='.'):
        r"Initialize the object, see class documentation for details."
        log.debug(u'NatHandler(%r)', pickle_dir)
        self._persistent_dir = pickle_dir
        ServiceHandler.__init__(self)
        self.forward = PortForwardHandler(self)
        self.snat = SNatHandler(self)
        self.masq = MasqHandler(self)


if __name__ == '__main__':

    logging.basicConfig(
        level   = logging.DEBUG,
        format  = '%(asctime)s %(levelname)-8s %(message)s',
        datefmt = '%H:%M:%S',
    )

    import os

    handler = NatHandler()

    def dump():
        print '-' * 80
        print 'Forwarded ports:'
        print handler.forward.show()
        print '-' * 10
        print 'SNat:'
        print handler.snat.show()
        print '-' * 10
        print 'Masq:'
        print handler.masq.show()
        print '-' * 80

    dump()
    handler.forward.add('eth0','tcp','80', '192.168.0.9', '8080')
    handler.forward.update(0, dst_net='192.168.0.188/32')
    handler.forward.add('eth0', 'udp', '53', '192.168.1.0')
    handler.commit()
    handler.stop()
    dump()
    handler.snat.add('eth0', '192.168.0.9')
    handler.snat.update(0, src_net='192.168.0.188/32')
    handler.snat.add('eth0', '192.168.1.0')
    handler.commit()
    dump()
    dump()
    handler.masq.add('eth0', '192.168.0.9/24')
    handler.masq.update(0, src_net='192.168.0.188/30')
    handler.masq.add('eth1', '192.168.1.0/24')
    handler.commit()
    dump()

    os.system('rm -f *.pkl')


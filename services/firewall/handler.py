# vim: set encoding=utf-8 et sw=4 sts=4 :

# TODO See if it's better (more secure) to execute commands via python instead
# of using script templates.

from os import path
import logging ; log = logging.getLogger('pymin.services.firewall')

from pymin.service.util import Restorable, ConfigWriter, ServiceHandler, \
                               TransactionalHandler

from rule import RuleHandler

__all__ = ('FirewallHandler',)


class FirewallHandler(Restorable, ConfigWriter, ServiceHandler,
                      TransactionalHandler):
    r"""FirewallHandler([pickle_dir[, config_dir]]) -> FirewallHandler instance.

    Handles firewall commands using iptables.

    pickle_dir - Directory where to write the persistent configuration data.

    config_dir - Directory where to store de generated configuration files.

    Both defaults to the current working directory.
    """

    handler_help = u"Manage firewall service"

    _persistent_attrs = ['rules']

    _restorable_defaults = dict(rules=list())

    _config_writer_files = 'iptables.sh'
    _config_writer_tpl_dir = path.join(path.dirname(__file__), 'templates')

    def __init__(self, pickle_dir='.', config_dir='.'):
        r"Initialize the object, see class documentation for details."
        log.debug(u'FirewallHandler(%r, %r)', pickle_dir, config_dir)
        self._persistent_dir = pickle_dir
        self._config_writer_cfg_dir = config_dir
        self._service_start = ('sh', path.join(self._config_writer_cfg_dir,
                                        self._config_writer_files))
        self._service_stop = ('iptables', '-t', 'filter', '-F')
        self._service_restart = self._service_start
        self._service_reload = self._service_start
        self._config_build_templates()
        ServiceHandler.__init__(self)
        self.rule = RuleHandler(self)

    def _get_config_vars(self, config_file):
        return dict(rules=self.rules)


if __name__ == '__main__':

    logging.basicConfig(
        level   = logging.DEBUG,
        format  = '%(asctime)s %(levelname)-8s %(message)s',
        datefmt = '%H:%M:%S',
    )

    import os

    fw_handler = FirewallHandler()

    def dump():
        print '-' * 80
        print 'Rules:'
        print fw_handler.rule.show()
        print '-' * 80

    dump()

    fw_handler.rule.add('input', 'drop', protocol='icmp')

    fw_handler.rule.update(0, dst='192.168.0.188/32')

    fw_handler.rule.add('output', 'accept', '192.168.1.0/24')

    fw_handler.commit()

    fw_handler.stop()

    dump()

    os.system('rm -f *.pkl iptables.sh')


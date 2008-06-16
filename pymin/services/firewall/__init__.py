# vim: set encoding=utf-8 et sw=4 sts=4 :

# TODO See if it's better (more secure) to execute commands via python instead
# of using script templates.

from os import path
from formencode import Invalid
from formencode.validators import OneOf, CIDR, Int
import logging ; log = logging.getLogger('pymin.services.firewall')

from pymin.item import Item
from pymin.validatedclass import Field
from pymin.dispatcher import Handler, handler, HandlerError
from pymin.services.util import Restorable, ConfigWriter, ServiceHandler, \
                                TransactionalHandler, ListSubHandler

__all__ = ('FirewallHandler', 'get_service')


def get_service(config):
    return FirewallHandler(config.firewall.pickle_dir, config.firewall.config_dir)


class UpOneOf(OneOf):
    def validate_python(self, value, state):
        value = value.upper()
        return OneOf.validate_python(self, value, state)

class Rule(Item):
    r"""Rule(chain, target[, src[, dst[, ...]]]) -> Rule instance.

    chain - INPUT, OUTPUT or FORWARD.
    target - ACCEPT, REJECT or DROP.
    src - Source subnet as IP/mask.
    dst - Destination subnet as IP/mask.
    protocol - ICMP, UDP, TCP or ALL.
    src_port - Source port (only for UDP or TCP protocols).
    dst_port - Destination port (only for UDP or TCP protocols).
    """
    chain = Field(UpOneOf(['INPUT', 'OUTPUT', 'FORWARD'], not_empty=True))
    target = Field(UpOneOf(['ACCEPT', 'REJECT', 'DROP'], not_empty=True))
    src = Field(CIDR(if_empty=None, if_missing=None))
    dst = Field(CIDR(if_empty=None, if_missing=None))
    protocol = Field(UpOneOf(['ICMP', 'UDP', 'TCP', 'ALL'], if_missing=None))
    src_port = Field(Int(min=0, max=65535, if_empty=None, if_missing=None))
    dst_port = Field(Int(min=0, max=65535, if_empty=None, if_missing=None))
    def chained_validator(self, fields, state):
        errors = dict()
        if fields['protocol'] not in ('TCP', 'UDP'):
            for name in ('src_port', 'dst_port'):
                if fields[name] is not None:
                    errors[name] = u"Should be None if protocol " \
                            "(%(protocol)s) is not TCP or UDP" % fields
        if errors:
            raise Invalid(u"You can't specify any ports if the protocol "
                        u'is not TCP or UDP', fields, state, error_dict=errors)

class RuleHandler(ListSubHandler):
    r"""RuleHandler(parent) -> RuleHandler instance :: Handle a list of rules.

    This class is a helper for FirewallHandler to do all the work related to rules
    administration.

    parent - The parent service handler.
    """

    handler_help = u"Manage firewall rules"

    _cont_subhandler_attr = 'rules'
    _cont_subhandler_class = Rule

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


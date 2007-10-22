# vim: set encoding=utf-8 et sw=4 sts=4 :

# TODO See if it's better (more secure) to execute commands via python instead
# of using script templates.

from os import path

from pymin.seqtools import Sequence
from pymin.dispatcher import Handler, handler, HandlerError
from pymin.services.util import Restorable, ConfigWriter, ServiceHandler, \
                                TransactionalHandler, ListSubHandler

__ALL__ = ('FirewallHandler',)

class Rule(Sequence):
    r"""Rule(chain, target[, src[, dst[, ...]]]) -> Rule instance.

    chain - INPUT, OUTPUT or FORWARD.
    target - ACCEPT, REJECT or DROP.
    src - Source subnet as IP/mask.
    dst - Destination subnet as IP/mask.
    protocol - ICMP, UDP, TCP or ALL.
    src_port - Source port (only for UDP or TCP protocols).
    dst_port - Destination port (only for UDP or TCP protocols).
    """

    def __init__(self, chain, target, src=None, dst=None, protocol=None,
                       src_port=None, dst_port=None):
        r"Initialize object, see class documentation for details."
        self.chain = chain
        self.target = target
        self.src = src
        self.dst = dst
        self.protocol = protocol
        # TODO Validate that src_port and dst_port could be not None only
        # if the protocol is UDP or TCP
        self.src_port = src_port
        self.dst_port = dst_port

    def update(self, chain=None, target=None, src=None, dst=None, protocol=None,
                       src_port=None, dst_port=None):
        r"update([chain[, ...]]) -> Update the values of a rule (see Rule doc)."
        if chain is not None: self.chain = chain
        if target is not None: self.target = target
        if src is not None: self.src = src
        if dst is not None: self.dst = dst
        if protocol is not None: self.protocol = protocol
        # TODO Validate that src_port and dst_port could be not None only
        # if the protocol is UDP or TCP
        if src_port is not None: self.src_port = src_port
        if dst_port is not None: self.dst_port = dst_port

    def as_tuple(self):
        r"Return a tuple representing the rule."
        return (self.chain, self.target, self.src, self.dst, self.protocol,
                    self.src_port, self.dst_port)

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

    import os

    fw_handler = FirewallHandler()

    def dump():
        print '-' * 80
        print 'Rules:'
        print fw_handler.rule.show()
        print '-' * 80

    dump()

    fw_handler.rule.add('input','drop','icmp')

    fw_handler.rule.update(0, dst='192.168.0.188/32')

    fw_handler.rule.add('output','accept', '192.168.1.0/24')

    fw_handler.commit()

    fw_handler.stop()

    dump()

    os.system('rm -f *.pkl iptables.sh')


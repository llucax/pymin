# vim: set encoding=utf-8 et sw=4 sts=4 :

# TODO See if it's better (more secure) to execute commands via python instead
# of using script templates.

from os import path

from seqtools import Sequence
from dispatcher import Handler, handler, HandlerError
from services.util import Restorable, ConfigWriter
from services.util import ServiceHandler, TransactionalHandler

__ALL__ = ('FirewallHandler', 'Error', 'RuleError', 'RuleAlreadyExistsError',
           'RuleNotFoundError')

class Error(HandlerError):
    r"""
    Error(command) -> Error instance :: Base FirewallHandler exception class.

    All exceptions raised by the FirewallHandler inherits from this one, so you can
    easily catch any FirewallHandler exception.

    message - A descriptive error message.
    """

    def __init__(self, message):
        r"Initialize the Error object. See class documentation for more info."
        self.message = message

    def __str__(self):
        return self.message

class RuleError(Error, KeyError):
    r"""
    RuleError(rule) -> RuleError instance.

    This is the base exception for all rule related errors.
    """

    def __init__(self, rule):
        r"Initialize the object. See class documentation for more info."
        self.message = 'Rule error: "%s"' % rule

class RuleAlreadyExistsError(RuleError):
    r"""
    RuleAlreadyExistsError(rule) -> RuleAlreadyExistsError instance.

    This exception is raised when trying to add a rule that already exists.
    """

    def __init__(self, rule):
        r"Initialize the object. See class documentation for more info."
        self.message = 'Rule already exists: "%s"' % rule

class RuleNotFoundError(RuleError):
    r"""
    RuleNotFoundError(rule) -> RuleNotFoundError instance.

    This exception is raised when trying to operate on a rule that doesn't
    exists.
    """

    def __init__(self, rule):
        r"Initialize the object. See class documentation for more info."
        self.message = 'Rule not found: "%s"' % rule

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

    def __cmp__(self, other):
        r"Compares two Rule objects."
        if self.chain == other.chain \
                and self.target == other.target \
                and self.src == other.src \
                and self.dst == other.dst \
                and self.protocol == other.protocol \
                and self.src_port == other.src_port \
                and self.dst_port == other.dst_port:
            return 0
        return cmp(id(self), id(other))

    def as_tuple(self):
        r"Return a tuple representing the rule."
        return (self.chain, self.target, self.src, self.dst, self.protocol,
                    self.src_port)

class RuleHandler(Handler):
    r"""RuleHandler(rules) -> RuleHandler instance :: Handle a list of rules.

    This class is a helper for FirewallHandler to do all the work related to rules
    administration.

    rules - A list of Rule objects.
    """

    def __init__(self, rules):
        r"Initialize the object, see class documentation for details."
        self.rules = rules

    @handler(u'Add a new rule.')
    def add(self, *args, **kwargs):
        r"add(rule) -> None :: Add a rule to the rules list (see Rule doc)."
        rule = Rule(*args, **kwargs)
        if rule in self.rules:
            raise RuleAlreadyExistsError(rule)
        self.rules.append(rule)

    @handler(u'Update a rule.')
    def update(self, index, *args, **kwargs):
        r"update(index, rule) -> None :: Update a rule (see Rule doc)."
        # TODO check if the modified rule is the same of an existing one
        index = int(index) # TODO validation
        try:
            self.rules[index].update(*args, **kwargs)
        except IndexError:
            raise RuleNotFoundError(index)

    @handler(u'Delete a rule.')
    def delete(self, index):
        r"delete(index) -> Rule :: Delete a rule from the list returning it."
        index = int(index) # TODO validation
        try:
            return self.rules.pop(index)
        except IndexError:
            raise RuleNotFoundError(index)

    @handler(u'Get information about a rule.')
    def get(self, index):
        r"get(rule) -> Rule :: Get all the information about a rule."
        index = int(index) # TODO validation
        try:
            return self.rules[index]
        except IndexError:
            raise RuleNotFoundError(index)

    @handler(u'Get information about all rules.')
    def show(self):
        r"show() -> list of Rules :: List all the complete rules information."
        return self.rules

class FirewallHandler(Restorable, ConfigWriter, ServiceHandler,
                      TransactionalHandler):
    r"""FirewallHandler([pickle_dir[, config_dir]]) -> FirewallHandler instance.

    Handles firewall commands using iptables.

    pickle_dir - Directory where to write the persistent configuration data.

    config_dir - Directory where to store de generated configuration files.

    Both defaults to the current working directory.
    """

    _persistent_vars = 'rules'

    _restorable_defaults = dict(rules=list())

    _config_writer_files = 'iptables.sh'
    _config_writer_tpl_dir = path.join(path.dirname(__file__), 'templates')

    def __init__(self, pickle_dir='.', config_dir='.'):
        r"Initialize the object, see class documentation for details."
        self._persistent_dir = pickle_dir
        self._config_writer_cfg_dir = config_dir
        self._service_start = path.join(self._config_writer_cfg_dir,
                                                    self._config_writer_files)
        self._service_stop = ('iptables', '-t', 'filter', '-F')
        self._service_restart = self._service_start
        self._service_reload = self._service_start
        self._config_build_templates()
        self._restore()
        self.rule = RuleHandler(self.rules)

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


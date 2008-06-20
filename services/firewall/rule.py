# vim: set encoding=utf-8 et sw=4 sts=4 :

from formencode import Invalid
from formencode.validators import OneOf, CIDR, Int

from pymin.item import Item
from pymin.validatedclass import Field
from pymin.service.util import ListSubHandler

__all__ = ('FirewallHandler',)


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


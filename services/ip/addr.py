# vim: set encoding=utf-8 et sw=4 sts=4 :

from pymin.service.util import DictComposedSubHandler, Address

__all__ = ('AddressHandler',)


class AddressHandler(DictComposedSubHandler):
    handler_help = u"Manage IP addresses"
    _comp_subhandler_cont = 'devices'
    _comp_subhandler_attr = 'addrs'
    _comp_subhandler_class = Address


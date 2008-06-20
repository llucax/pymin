# vim: set encoding=utf-8 et sw=4 sts=4 :

from pymin.seqtools import Sequence
from pymin.dispatcher import handler
from pymin.service.util import ListComposedSubHandler

__all__ = ('RouteHandler',)


class Route(Sequence):
    def __init__(self, net_addr, prefix, gateway):
        self.net_addr = net_addr
        self.prefix = prefix
        self.gateway = gateway

    def update(self, net_addr=None, prefix=None, gateway=None):
        if net_addr is not None: self.net_addr = net_addr
        if prefix is not None: self.prefix = prefix
        if gateway is not None: self.gateway = gateway

    def as_tuple(self):
        return(self.net_addr, self.prefix, self.gateway)

    def __cmp__(self, other):
        if self.net_addr == other.net_addr \
                and self.prefix == other.prefix \
                and self.gateway == other.gateway:
            return 0
        return cmp(id(self), id(other))

class RouteHandler(ListComposedSubHandler):
    handler_help = u"Manage IP routes"
    _comp_subhandler_cont = 'devices'
    _comp_subhandler_attr = 'routes'
    _comp_subhandler_class = Route

    @handler(u'Adds a route to : ip route add <net_addr> <prefix> <gateway> [device]')
    def add(self, net_addr, prefix, gateway, dev=None):
        if dev is not None:
            ListComposedSubHandler.add(self, dev, net_addr, prefix, gateway)
        else:
            r = Route(net_addr, prefix, gateway)
            if not r in self.parent.no_device_routes:
                self.parent.no_device_routes.append(r)

    @handler("Deletes a route : ip route delete <route_number_in_show> [dev]")
    def delete(self, index, dev=None):
        if dev is not None:
            ListComposedSubHandler.delete(self, dev, index)
        else:
            i = int(index)
            del self.parent.no_device_routes[i]

    @handler("Shows routes : ip route show [dev]")
    def show(self, dev=None):
        if dev is not None:
            return ListComposedSubHandler.show(self, dev)
        else:
            return self.parent.no_device_routes


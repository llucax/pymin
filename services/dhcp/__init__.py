# vim: set encoding=utf-8 et sw=4 sts=4 :

try:
    import cPickle as pickle
except ImportError:
    import pickle

from mako.template import Template
from mako.runtime import Context

class Host:
    def __init__(self, name, ip, mac):
        self.name = name
        self.ip = ip
        self.mac = mac
    def __repr__(self):
        return 'Host(name="%s", ip="%s", mac="%s")' % (
                     self.name, self.ip, self.mac)

class HostHandler:

    def __init__(self, hosts):
        self.hosts = hosts

    def add(self, name, ip, mac):
        #deberia indexar por hostname o por ip? o por mac? :)
        # Mejor por nada...
        self.hosts[name] = Host(name, ip, mac)

    def update(self, name, ip=None, mac=None):
        if ip is not None:
            self.hosts[name].ip = ip
        if mac is not None:
            self.hosts[name].mac = mac

    def delete(self, name):
        del self.hosts[name]

    def list(self):
        return ','.join(self.hosts)

    def show(self):
        hosts = self.hosts.values()
        return '\n'.join('%s,%s,%s' % (h.name, h.ip, h.mac) for h in hosts)

class DhcpHandler:
    r"""class that handles DHCP service using dhcpd program"""

    def __init__(self):
        self.hosts = dict()
        self.vars = dict(
            domain_name = 'my_domain_name',
            dns_1       = 'my_ns1',
            dns_2       = 'my_ns2',
            net_address = '192.168.0.0',
            net_mask    = '255.255.255.0',
            net_start   = '192.168.0.100',
            net_end     = '192.168.0.200',
            net_gateway = '192.168.0.1',
        )
        self.host = HostHandler(self.hosts)

    def set(self, param, value):
        if param in self.vars:
            self.vars[param] = value
        else:
            raise KeyError("Parameter " + param + " not found")

    def list(self):
        return ','.join(self.vars)

    def show(self):
        return '\n'.join(('%s,%s' % (k, v) for (k, v) in self.vars.items()))

    def start(self):
        #esto seria para poner en una interfaz
        #y seria el hook para arrancar el servicio
        pass

    def stop(self):
        #esto seria para poner en una interfaz
        #y seria el hook para arrancar el servicio
        pass

    def commit(self):
        #esto seria para poner en una interfaz
        #y seria que hace el pickle deberia llamarse
        #al hacerse un commit
        pickle.dump(self.vars, file('pickled/vars.pkl', 'wb'), 2)
        pickle.dump(self.hosts, file('pickled/hosts.pkl', 'wb'), 2)
        tpl = Template(filename='templates/dhcpd.conf')
        ctx = Context(file('generated/dhcpd.conf', 'w'),
                        hosts=self.hosts.values(), **self.vars)
        tpl.render_context(ctx)

if __name__ == '__main__':

    config = DhcpHandler()

    config.host.add('my_name','192.168.0.102','00:12:ff:56')

    config.host.update('my_name','192.168.0.192','00:12:ff:56')

    config.host.add('nico','192.168.0.188','00:00:00:00')

    config.set('domain_name','baryon.com.ar')

    try:
        config.set('sarasa','baryon.com.ar')
    except KeyError, e:
        print 'Error:', e

    config.commit()

    print 'Variables:', config.list()
    print config.show()

    print 'Hosts:', config.host.list()
    print config.host.show()

    vars = pickle.load(file('pickled/vars.pkl'))
    hosts = pickle.load(file('pickled/hosts.pkl'))
    print 'Pickled vars:', vars
    print 'Pickled hosts:', hosts


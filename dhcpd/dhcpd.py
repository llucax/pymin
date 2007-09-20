
import pickle

class ParamsError(Exception):
    def __init__(self,reason):
        self.reason = reason

    def __str__(self):
        return repr(reason)

class dhcpd:
    "class that handles dhcpd config"

    def __init__(self):
        self.host_list = dict()
        self.glob = {   'domain_name' : 'my_domain_name',
                        'dns_1'       : 'my_ns1',
                        'dns_2'       : 'my_ns2',
                        'net_address' : '192.168.0.0',
                        'net_mask'    : '255.255.255.0',
                        'net_start'   : '192.168.0.100',
                        'net_end'     : '192.168.0.200',
                        'net_gateway' : '192.168.0.1'}
        

    def to_file_format(self):
        #bajo los parametros globales
        glob_file = open('dhcpd_global.template','r')
        glob_tmp = glob_file.read()
        glob_file.close()
        conf = glob_tmp % self.glob
        #bajo los hosts
        host_file = open('dhcpd_host.template','r')
        host_tmp = host_file.read()
        host_file.close()
        for h , v in self.host_list.iteritems():
            conf = conf + '\n' + (host_tmp % v)
        return conf

    def add_host(self, args):
        #deberia indexar por hostname o por ip?
        if len(args) == 3:
            self.host_list[args[0]] = {"host_name": args[0], "host_ip": args[1], "host_mac": args[2]}
        else:
            raise ParamsError('Wrong number of parameters')

    def mod_host(self, args):
        #deberia indexar por hostname o por ip?
        if len(args) == 3:
            self.host_list[args[0]] = {"host_name": args[0], "host_ip": args[1], "host_mac": args[2]}
        else:
            raise ParamsError('Wrong number of parameters')

    def remove_host(self, hostname):
        if hostname in self.host_list:
            del(self.host_list[hostname])
        else:
            raise ParamsError("No such host")

    def set(self, pair):
        if pair[0] in self.glob:
            self.glob[pair[0]] = pair[1]
        else:
            raise ParamsError("Parameter " + pair[0] + " not found")
        
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
        output = open('dhcpd_config.pkl', 'wb')
        pickle.dump(config, output)
        output.close()

    def show_params(self):
        string = ''
        for k , v in self.glob.iteritems():
            string = string + k + ' : ' + v + '\n'
        return string

    def show_hosts(self):
        string = ''
        for k , v in self.host_list.iteritems():
            string = string + k + ' : ' +  v["host_ip"] + ' : ' + v["host_mac"] + '\n'
        return string


if __name__ == '__main__':
    
    config = dhcpd()

    try :
        arguments = ('my_name','192.168.0.102','00:12:ff:56')
        config.add_host(arguments)
        
        arguments = ('my_name','192.168.0.192','00:12:ff:56')
        config.mod_host(arguments)

        arguments = ('nico','192.168.0.188','00:00:00:00')
        config.add_host(arguments)

        config.set(('domain_name','baryon.com.ar'))
        config.set(('sarasa','baryon.com.ar'))

    except ParamsError, inst:
        print inst.reason
        
    config.commit()
    
    conf_file = open('dhcpd.conf','w')
    conf_file.write(config.to_file_format())
    conf_file.close()

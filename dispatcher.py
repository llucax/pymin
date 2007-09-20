# vim: set et sts=4 sw=4 encoding=utf-8 :

class BadRouteError(Exception):

	def __init__(self,cmd):
		self.cmd = cmd

	def __str__(self):
		return repr(cmd)

class CommandNotFoundError(Exception):

	def __init__(self,cmd):
		self.cmd = cmd

	def __str__(self):
		return repr(cmd)

class Dispatcher:

	def __init__(self, routes=dict()):
		self.routes = routes

	def dispatch(self, route):
		route = route.split() # TODO considerar comillas
		try:
			handler = self.routes[route[0]]
			route = route[1:]
			while not callable(handler):
				handler = getattr(handler, route[0])
				route = route[1:]
			handler(*route)

		except KeyError:
			raise CommandNotFoundError(route[0])
		except AttributeError:
			raise BadRouteError(route[0])
		except IndexError:
			pass


def test_func(*args):
  	print 'func:', args


class TestClassSubHandler:

	def subcmd(self, *args):
		print 'class.subclass.subcmd:', args


class TestClass:

	def cmd1(self, *args):
		print 'class.cmd1:', args

	def cmd2(self, *args):
		print 'class.cmd2:', args

	subclass = TestClassSubHandler()


if __name__ == '__main__':

    d = Dispatcher(dict(
            func=test_func,
            inst=TestClass(),
    ))

    d.dispatch('func arg1 arg2 arg3')
    d.dispatch('inst cmd1 arg1 arg2 arg3 arg4')
    d.dispatch('inst subclass subcmd arg1 arg2 arg3 arg4 arg5')

# Ideas / TODO:
#
# * Soportar comillas para argumentos con espacios y otros caracteres, onda:
#   'misc set motd "Hola!\nEste es el servidor de garombia"'
#
# * Soportar keyword arguments, onda que:
#   'dns set pepe=10.10.10.1 juan=10.10.10.2'
#   se mapee a algo como: dns.set(pepe='10.10.10.1', juan='10.10.10.2')
#
# Estas cosas quedan sujetas a necesitada y a definición del protocolo.
# Para mí lo ideal es que el protocolo de red sea igual que la consola del
# usuario, porque después de todo no va a ser más que eso, mandar comanditos.
#
# Por otro lado, el cliente de consola, por que no es el cliente web pero
# accedido via ssh usando un navegador de texto como w3m???


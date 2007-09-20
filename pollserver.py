# vim: set encoding=utf-8 et sw=4 sts=4 :

import signal
import select
from sys import exit

import dispatcher as dis
import udp_server as us

def quit(signum, frame):
    print "Shuting down ..."
    exit(0)

signal.signal(signal.SIGINT, quit)
signal.signal(signal.SIGTERM, quit)

server = us.UDPServer(9999)

poll = select.poll()
poll.register(server.sock.fileno(), select.POLLIN | select.POLLPRI)

d = dis.Dispatcher(dict(
					func=dis.test_func,
				   	inst=dis.TestClass()
				   ))

def handle_recv(sock):
	(msg, addr) = sock.recvfrom(65535)
	try:
		d.dispatch(msg)
	except dis.BadRouteError, inst:
		sock.sendto('Bad route from : ' + inst.cmd + '\n', addr)
	except dis.CommandNotFoundError, inst:
		sock.sendto('Command not found : ' + inst.cmd + '\n', addr)

while True:
    l = poll.poll()
    handle_recv(server.sock)


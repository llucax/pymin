# vim: set encoding=utf-8 et sw=4 sts=4 :

import socket as s

class UDPServer:
	"Udp server class"

	def __init__(self, port):
		self.sock = s.socket(s.AF_INET, s.SOCK_DGRAM)
		self.sock.setsockopt(s.SOL_SOCKET, s.SO_REUSEADDR, 1)
		self.sock.bind(('', port))
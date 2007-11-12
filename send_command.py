#!/usr/bin/env python

import sys
import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

host = sys.argv[1]
port = int(sys.argv[2])

s.bind(('', port+1))

s.sendto(sys.stdin.read(), 0, (host, port))

print

print s.recvfrom(4096)[0]


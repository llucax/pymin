# vim: set encoding=utf-8 et sw=4 sts=4 :

r"""
Python Administration Daemon.

Python Administration Daemon is an modular, extensible administration tool
to administrate a set of services remotely (or localy) throw a simple
command-line.
"""

import signal
import socket
from dispatcher import Dispatcher
from eventloop import EventLoop, LoopInterruptedError

class PyminDaemon(EventLoop):
    r"""PyminDaemon(bind_addr, routes) -> PyminDaemon instance

    This class is well suited to run as a single process. It handles
    signals for controlled termination (SIGINT and SIGTERM), as well as
    a user signal to reload the configuration files (SIGUSR1).

    bind_addr - is a tuple of (ip, port) where to bind the UDP socket to.

    routes - is a dictionary where the key is a command string and the value
             is the command handler. This is passed directly to the Dispatcher.

    Here is a simple usage example:

    >>> def test_handler(*args): print 'test:', args
    >>> PyminDaemon(('', 9999), dict(test=test_handler)).run()
    """

    def __init__(self, bind_addr, routes):
        r"""Initialize the PyminDaemon object.

        See PyminDaemon class documentation for more info.
        """
        # Create and bind socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(bind_addr)
        # Create EventLoop
        EventLoop.__init__(self, sock)
        # Create Dispatcher
        self.dispatcher = Dispatcher(routes)
        # Signal handling
        def quit(signum, frame):
            print "Shuting down ..."
            self.stop() # tell main event loop to stop
        def reload_config(signum, frame):
            print "Reloading configuration..."
            # TODO iterate handlers list propagating reload action
        signal.signal(signal.SIGINT, quit)
        signal.signal(signal.SIGTERM, quit)
        signal.signal(signal.SIGUSR1, reload_config)

    def handle(self):
        r"handle() -> None :: Handle incoming events using the dispatcher."
        (msg, addr) = self.file.recvfrom(65535)
        result = self.dispatcher.dispatch(msg)
        if result is None:
            msg = 'OK 0'
        else:
            msg = 'OK %d\n%s' % (len(str(result)), result)
        self.file.sendto(msg, addr)
        #try:
        #    d.dispatch(msg)
        #except dis.BadRouteError, inst:
        #    sock.sendto('Bad route from : ' + inst.cmd + '\n', addr)
        #except dis.CommandNotFoundError, inst:
        #    sock.sendto('Command not found : ' + inst.cmd + '\n', addr)

    def run(self):
        r"run() -> None :: Run the event loop (shortcut to loop())"
        try:
            return self.loop()
        except LoopInterruptedError, e:
            pass

if __name__ == '__main__':

    @handler
    def test_handler(*args):
        print 'test:', args

    PyminDaemon(('', 9999), dict(test=test_handler)).run()


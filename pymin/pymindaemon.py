# vim: set encoding=utf-8 et sw=4 sts=4 :

r"""
Python Administration Daemon.

Python Administration Daemon is an modular, extensible administration tool
to administrate a set of services remotely (or localy) throw a simple
command-line.
"""

import signal
import socket

from pymin.dispatcher import handler
from pymin import dispatcher
from pymin import eventloop
from pymin import serializer

class PyminDaemon(eventloop.EventLoop):
    r"""PyminDaemon(root, bind_addr) -> PyminDaemon instance

    This class is well suited to run as a single process. It handles
    signals for controlled termination (SIGINT and SIGTERM), as well as
    a user signal to reload the configuration files (SIGUSR1).

    root - the root handler. This is passed directly to the Dispatcher.

    bind_addr - is a tuple of (ip, port) where to bind the UDP socket to.

    Here is a simple usage example:

    >>> from pymin import dispatcher
    >>> class Root(dispatcher.Handler):
            @handler('Test command.')
            def test(self, *args):
                print 'test:', args
    >>> PyminDaemon(Root(), ('', 9999)).run()
    """

    def __init__(self, root, bind_addr=('', 9999), timer=1):
        r"""Initialize the PyminDaemon object.

        See PyminDaemon class documentation for more info.
        """
        # Create and bind socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(bind_addr)
        # Create EventLoop
        eventloop.EventLoop.__init__(self, sock, timer=timer)
        # Create Dispatcher
        #TODO root.pymin = PyminHandler()
        self.dispatcher = dispatcher.Dispatcher(root)
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
        try:
            result = self.dispatcher.dispatch(unicode(msg, 'utf-8'))
            if result is not None:
                result = serializer.serialize(result)
            response = u'OK '
        except dispatcher.Error, e:
            result = unicode(e) + u'\n'
            response = u'ERROR '
        except Exception, e:
            import traceback
            result = u'Internal server error\n'
            traceback.print_exc() # TODO logging!
            response = u'ERROR '
        if result is None:
            response += u'0\n'
        else:
            response += u'%d\n%s' % (len(result), result)
        self.file.sendto(response.encode('utf-8'), addr)

    def handle_timer(self):
        r"handle_timer() -> None :: Call handle_timer() on handlers."
        self.dispatcher.root.handle_timer()

    def run(self):
        r"run() -> None :: Run the event loop (shortcut to loop())"
        try:
            return self.loop()
        except eventloop.LoopInterruptedError, e:
            pass

if __name__ == '__main__':

    class Root(dispatcher.Handler):
        @handler(u"Print all the arguments, return nothing.")
        def test(self, *args):
            print 'test:', args
        @handler(u"Echo the message passed as argument.")
        def echo(self, message):
            print 'echo:', message
            return message

    PyminDaemon(Root()).run()


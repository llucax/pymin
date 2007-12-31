# vim: set encoding=utf-8 et sw=4 sts=4 :

r"""
Python Administration Daemon.

Python Administration Daemon is an modular, extensible administration tool
to administrate a set of services remotely (or localy) throw a simple
command-line.
"""

import signal
import socket
import formencode
import logging ; log = logging.getLogger('pymin.pymindaemon')

from pymin.dispatcher import handler
from pymin import dispatcher
from pymin import eventloop
from pymin import serializer
from pymin import procman

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

    The daemon then will be listening to messages to UDP port 9999. Messages
    will be dispatcher throgh the pymin.dispatcher mechanism. If all goes ok,
    an OK response is sent. If there was a problem, an ERROR response is sent.

    The general syntax of responses is::

        (OK|ERROR) LENGTH
        CSV MESSAGE

    So, first is a response code (OK or ERROR), then it comes the length of
    the CSV MESSAGE (the bufer needed to receive the rest of the message).

    CSV MESSAGE is the body of the response, which it could be void (if lenght
    is 0), a simple string (a CVS with only one column and row), a single row
    or a full "table" (a CSV with multiple rows and columns).

    There are 2 kind of errors considered "normal": dispatcher.Error and
    formencode.Invalid. In general, response bodies of errors are simple
    strings, except, for example, for formencode.Invalid errors where an
    error_dict is provided. In that case the error is a "table", where the
    first colunm is the name of an invalid argument, and the second is the
    description of the error for that argument. Any other kind of exception
    raised by the handlers will return an ERROR response with the description
    "Internal server error".

    All messages (requests and responses) should be UTF-8 encoded and the CVS
    responses are formated in "Excel" format, as known by the csv module.
    """

    def __init__(self, root, bind_addr=('', 9999), timer=1):
        r"""Initialize the PyminDaemon object.

        See PyminDaemon class documentation for more info.
        """
        log.debug(u'PyminDaemon(%r, %r, %r)', root, bind_addr, timer)
        # Timer timeout time
        self.timer = timer
        # Create and bind socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(bind_addr)
        # Signal handling
        def quit(loop, signum):
            log.debug(u'PyminDaemon quit() handler: signal %r', signum)
            log.info(u'Shutting down...')
            loop.stop() # tell main event loop to stop
        def reload_config(loop, signum):
            log.debug(u'PyminDaemon reload_config() handler: signal %r', signum)
            log.info(u'Reloading configuration...')
            # TODO iterate handlers list propagating reload action
        def timer(loop, signum):
            loop.handle_timer()
            signal.alarm(loop.timer)
        def child(loop, signum):
            procman.sigchild_handler(signum)
        # Create EventLoop
        eventloop.EventLoop.__init__(self, sock, signals={
                signal.SIGINT: quit,
                signal.SIGTERM: quit,
                signal.SIGUSR1: reload_config,
                signal.SIGALRM: timer,
                signal.SIGCHLD: child,
            })
        # Create Dispatcher
        #TODO root.pymin = PyminHandler()
        self.dispatcher = dispatcher.Dispatcher(root)

    def handle(self):
        r"handle() -> None :: Handle incoming events using the dispatcher."
        (msg, addr) = self.file.recvfrom(65535)
        log.debug(u'PyminDaemon.handle: message %r from %r', msg, addr)
        response = u'ERROR'
        try:
            result = self.dispatcher.dispatch(unicode(msg, 'utf-8'))
            if result is not None:
                result = serializer.serialize(result)
            response = u'OK'
        except dispatcher.Error, e:
            result = unicode(e) + u'\n'
        except formencode.Invalid, e:
            if e.error_dict:
                result = serializer.serialize(e.error_dict)
            else:
                result = unicode(e) + u'\n'
        except Exception, e:
            import traceback
            result = u'Internal server error\n'
            log.exception(u'PyminDaemon.handle: unhandled exception')
        if result is None:
            response += u' 0\n'
        else:
            response += u' %d\n%s' % (len(result), result)
        log.debug(u'PyminDaemon.handle: response %r to %r', response, addr)
        self.file.sendto(response.encode('utf-8'), addr)

    def handle_timer(self):
        r"handle_timer() -> None :: Call handle_timer() on handlers."
        self.dispatcher.root.handle_timer()

    def run(self):
        r"run() -> None :: Run the event loop (shortcut to loop())"
        log.debug(u'PyminDaemon.loop()')
        # Start the timer
        self.handle_timer()
        signal.alarm(self.timer)
        # Loop
        try:
            return self.loop()
        except eventloop.LoopInterruptedError, e:
            log.debug(u'PyminDaemon.loop: interrupted')
            pass

if __name__ == '__main__':

    logging.basicConfig(
        level   = logging.DEBUG,
        format  = '%(asctime)s %(levelname)-8s %(message)s',
        datefmt = '%H:%M:%S',
    )

    class Scheme(formencode.Schema):
        mod = formencode.validators.OneOf(['upper', 'lower'], if_empty='lower')
        ip = formencode.validators.CIDR

    class Root(dispatcher.Handler):
        @handler(u"Print all the arguments, return nothing.")
        def test(self, *args):
            print 'test:', args
        @handler(u"Echo the message passed as argument.")
        def echo(self, message, mod=None, ip=None):
            vals = Scheme.to_python(dict(mod=mod, ip=ip))
            mod = vals['mod']
            ip = vals['ip']
            message = getattr(message, mod)()
            print 'echo:', message
            return message

    PyminDaemon(Root()).run()


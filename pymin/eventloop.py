# vim: set encoding=utf-8 et sw=4 sts=4 :

r"""
A simple event loop.

Please see EventLoop class documentation for more info.
"""

import select
import errno
import signal
from select import POLLIN, POLLPRI, POLLERR
import logging ; log = logging.getLogger('pymin.eventloop')

__ALL__ = ('EventLoop', 'LoopInterruptedError')

class LoopInterruptedError(RuntimeError):
    r"""
    LoopInterruptedError(select_error) -> LoopInterruptedError instance.

    This class is raised when the event loop is interrupted in an unexpected
    way. It wraps a select error, which can be accessed using the 'select_error'
    attribute.
    """

    def __init__(self, select_error):
        r"""Initialize the object.

        See the class documentation for more info.
        """
        self.select_error = select_error

    def __repr__(self):
        r"repr(obj) -> Object representation."
        return 'LoopInterruptedError(select_error=%r)' % self.select_error

    def __str__(self):
        r"str(obj) -> String representation."
        return 'Loop interrupted: %s' % self.select_error

# Flag to know if a signal was caught
signals = list()

# Alarm Signal handler
def signal_handler(signum, stack_frame):
    global signals
    signals.append(signum)

class EventLoop:
    r"""EventLoop(file[, handler[, signals]]]) -> EventLoop.

    This class implements a simple event loop based on select module.
    It "listens" to activity a single 'file' object (a file, a pipe,
    a socket, or even a simple file descriptor) and calls a 'handler'
    function (or the handle() method if you prefer subclassing) every
    time the file is ready for reading (or has an error).

    'signals' is a dictionary with signals to be handled by the loop,
    where keys are signal numbers and values are callbacks (which takes
    2 arguments, first the event loop that captured the signal, and then
    the captured signal number). Callbacks can be None if all signals
    are handled by the handle_signal() member function.

    This is a really simple example of usage using a hanlder callable:

    >>> import os
    >>> def handle(event_loop):
            data = os.read(event_loop.fileno, 100)
            os.write(1, 'Received message: %r\n' % data)
    >>> p = EventLoop(0, handle)
    >>> p.loop(once=True)

    In this example only one event is handled (see the 'once' argument
    of loop).

    A more complex example, making a subclass and explicitly stopping
    the loop, looks something like this:

    >>> class Test(EventLoop):
    >>>     def handle(self):
    >>>         data = os.read(self.fileno, 100)
    >>>         os.write(1, 'Received message: %r\n' % data)
    >>>     def handle_signal(self, signum):
    >>>         os.write(1, 'Signal %d received, stopping\n' % signum)
    >>>         self.stop()
    >>> p = Test(0, signals={signal.SIGTERM: None, signal.SIGINT: None})
    >>> p.loop()

    This example loops until the user enter interrupts the program (by
    pressing Ctrl-C) or untile the program is terminated by a TERM signal
    (kill) when stop() is called and the event loop is exited.
    """

    def __init__(self, file, handler=None, signals=None):
        r"""Initialize the EventLoop object.

        See EventLoop class documentation for more info.
        """
        log.debug(u'EventLoop(%r, %r, %r)', file, handler, signals)
        self.poll = select.poll()
        self._stop = False
        self.__register(file)
        self.handler = handler
        self.signals = dict()
        if signals is None:
            signals = dict()
        for (signum, sighandler) in signals.items():
            self.set_signal(signum, sighandler)

    def __register(self, file):
        r"__register(file) -> None :: Register a new file for polling."
        self._file = file
        self.poll.register(self.fileno, POLLIN | POLLPRI | POLLERR)

    def set_signal(self, signum, sighandler):
        prev = self.signals.get(signum, None)
        # If the signal was not already handled, handle it
        if signum not in self.signals:
            signal.signal(signum, signal_handler)
        self.signals[signum] = sighandler
        return prev

    def get_signal_handler(self, signum):
        return self.signals[signum]

    def unset_signal(self, signum):
        prev = self.signals[signum]
        # Restore the default handler
        signal.signal(signum, signal.SIG_DFL)
        return prev

    def set_file(self, file):
        r"""set_file(file) -> None :: New file object to be monitored

        Unregister the previous file object being monitored and register
        a new one.
        """
        self.poll.unregister(self.fileno)
        self.__register(file)

    def get_file(self):
        r"get_file() -> file object/int :: Get the current file object/fd."
        return self._file

    file = property(get_file, set_file, doc='File object (or descriptor)')

    def get_fileno(self):
        r"get_fileno() -> int :: Get the current file descriptor"
        if hasattr(self.file, 'fileno'):
            return self.file.fileno()
        return self.file

    fileno = property(get_fileno, doc='File descriptor (never a file object)')

    def stop(self):
        r"""stop() -> None :: Stop the event loop.

        The event loop will be interrupted as soon as the current handler
        finishes.
        """
        log.debug(u'EventLoop.stop()')
        self._stop = True

    def loop(self, once=False):
        r"""loop([once]) -> None :: Wait for events.

        Wait for events and handle then when they arrive. If once is True,
        then only 1 event is processed and then this method returns.
        """
        log.debug(u'EventLoop.loop(%s)', once)
        # List of pending signals
        global signals
        while True:
            try:
                log.debug(u'EventLoop.loop: polling')
                res = self.poll.poll()
            except select.error, e:
                # The error is not an interrupt caused by a signal, then raise
                if e.args[0] != errno.EINTR or not signals:
                    raise LoopInterruptedError(e)
            # If we have signals to process, we just do it
            have_signals = bool(signals)
            while signals:
                signum = signals.pop(0)
                log.debug(u'EventLoop.loop: processing signal %d...', signum)
                self.handle_signal(signum)
            # No signals to process, execute the regular handler
            if not have_signals:
                log.debug(u'EventLoop.loop: processing event...')
                self.handle()
            # Look if we have to stop
            if self._stop or once:
                log.debug(u'EventLoop.loop: stopped')
                self._stop = False
                break

    def handle(self):
        r"handle() -> None :: Handle file descriptor events."
        self.handler(self)

    def handle_signal(self, signum):
        r"handle_signal(signum) -> None :: Handles signals."
        self.signals[signum](self, signum)

if __name__ == '__main__':

    logging.basicConfig(
        level   = logging.DEBUG,
        format  = '%(asctime)s %(levelname)-8s %(message)s',
        datefmt = '%H:%M:%S',
    )

    import os
    import time

    def handle(event_loop):
        data = os.read(event_loop.fileno, 100)
        os.write(1, 'Received message: %r\n' % data)

    p = EventLoop(0, handle)

    os.write(1, 'Say something once:\n')
    p.loop(once=True)
    os.write(1, 'Great!\n')

    class Test(EventLoop):
        def handle(self):
            data = os.read(self.fileno, 100)
            os.write(1, 'Received message: %r\n' % data)
        def handle_signal(self, signum):
            os.write(1, 'Signal %d received, stopping\n' % signum)
            self.stop()

    p = Test(0, signals={signal.SIGTERM: None, signal.SIGINT: None})

    os.write(1, 'Say a lot of things, then press Ctrl-C or kill me to stop: ')
    p.loop()
    os.write(1, 'Ok, bye!\n')


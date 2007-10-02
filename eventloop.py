# vim: set encoding=utf-8 et sw=4 sts=4 :

r"""
A simple event loop.

Please see EventLoop class documentation for more info.
"""

import select
from select import POLLIN, POLLPRI, POLLERR

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

class EventLoop:
    r"""EventLoop(file[, handler]) -> EventLoop instance

    This class implements a simple event loop based on select module.
    It "listens" to activity a single 'file' object (a file, a pipe,
    a socket, or even a simple file descriptor) and calls a 'handler'
    function (or the handle() method if you prefer subclassing) every
    time the file is ready for reading (or has an error).

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
    >>>         if data == 'q\n':
    >>>             self.stop()
    >>>         else:
    >>>             os.write(1, 'Received message: %r\n' % data)
    >>> p = Test(0)
    >>> p.loop()

    This example loops until the user enters a single "q", when stop()
    is called and the event loop is exited.
    """

    def __init__(self, file, handler=None):
        r"""Initialize the EventLoop object.

        See EventLoop class documentation for more info.
        """
        self.poll = select.poll()
        self._stop = False
        self.__register(file)
        self.handler = handler

    def __register(self, file):
        r"__register(file) -> None :: Register a new file for polling."
        self._file = file
        self.poll.register(self.fileno, POLLIN | POLLPRI | POLLERR)

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
        self._stop = True

    def loop(self, once=False):
        r"""loop([once]) -> None :: Wait for events.

        Wait for events and handle then when they arrive. If once is True,
        then only 1 event is processed and then this method returns.
        """
        while True:
            try:
                res = self.poll.poll()
            except select.error, e:
                raise LoopInterruptedError(e)
            if self.handler is not None:
                self.handler(self)
            else:
                self.handle()
            if self._stop or once:
                self._stop = False
                break

    def handle(self):
        r"handle() -> None :: Abstract method to be overriden to handle events."
        raise NotImplementedError

if __name__ == '__main__':

    import os

    def handle(event_loop):
        data = os.read(event_loop.fileno, 100)
        os.write(1, 'Received message: %r\n' % data)

    p = EventLoop(0, handle)

    os.write(1, 'Say something once: ')
    p.loop(once=True)
    os.write(1, 'Great!\n')

    class Test(EventLoop):
        def handle(self):
            data = os.read(self.fileno, 100)
            if data == 'q\n':
                self.stop()
            else:
                os.write(1, 'Received message: %r\n' % data)

    p = Test(0)

    os.write(1, 'Say a lot of things, then press write just "q" to stop: ')
    p.loop()
    os.write(1, 'Ok, bye!\n')


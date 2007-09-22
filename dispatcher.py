# vim: set et sts=4 sw=4 encoding=utf-8 :

r"""
Command dispatcher.

This module provides a convenient and extensible command dispatching mechanism.
It's based on Zope or Cherrypy dispatching (but implemented from the scratch)
and translates commands to functions/objects/methods.
"""

class Error(RuntimeError):
    r"""
    Error(command) -> Error instance :: Base dispatching exceptions class.

    All exceptions raised by the Dispatcher inherits from this one, so you can
    easily catch any dispatching exception.

    command - is the command that raised the exception.
    """

    def __init__(self, command):
        r"""Initialize the Error object.

        See Error class documentation for more info.
        """
        self.command = command

    def __str__(self):
        return repr(self.command)

class CommandNotFoundError(Error):
    r"""
    CommandNotFoundError(command) -> CommandNotFoundError instance

    This exception is raised when the command received can't be dispatched
    because there is no handlers to process it.
    """
    pass

class Dispatcher:
    r"""Dispatcher([routes]) -> Dispatcher instance :: Command dispatcher

    This class provides a modular and extensible dispatching mechanism. You
    can specify root 'routes' (as a dict where the key is the string of the
    root command and the value is a callable object to handle that command,
    or a subcommand if the callable is an instance and the command can be
    sub-routed).

    The command can have arguments, separated by (any number of) spaces.

    The dispatcher tries to route the command as deeply as it can, passing
    the other "path" components as arguments to the callable. To route the
    command it inspects the callable attributes to find a suitable callable
    attribute to handle the command in a more specific way, and so on.

    Example:
    >>> d = Dispatcher(dict(handler=some_handler))
    >>> d.dispatch('handler attribute method arg1 arg2')

    If 'some_handler' is an object with an 'attribute' that is another
    object which has a method named 'method', then
    some_handler.attribute.method('arg1', 'arg2') will be called. If
    some_handler is a function, then some_handler('attribute', 'method',
    'arg1', 'arg2') will be called. The handler "tree" can be as complex
    and deep as you want.

    If some command can't be dispatched (because there is no root handler or
    there is no matching callable attribute), a CommandNotFoundError is raised.
    """

    def __init__(self, routes=dict()):
        r"""Initialize the Dispatcher object.

        See Dispatcher class documentation for more info.
        """
        self.routes = routes

    def dispatch(self, route):
        r"""dispatch(route) -> None :: Dispatch a command string.

        This method searches for a suitable callable object in the routes
        "tree" and call it, or raises a CommandNotFoundError if the command
        can't be dispatched.
        """
        route = route.split() # TODO support "" and keyword arguments
        if not route:
            raise CommandNotFoundError('') # TODO better error reporting
        handler = self.routes.get(route[0], None)
        route = route[1:]
        while not callable(handler):
            if not route:
                raise CommandNotFoundError('XXX') # TODO better error reporting
            if not hasattr(handler, route[0]):
                raise CommandNotFoundError(route[0]) # TODO better error rep.
            handler = getattr(handler, route[0])
            route = route[1:]
        handler(*route)


if __name__ == '__main__':

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

    d = Dispatcher(dict(
            func=test_func,
            inst=TestClass(),
    ))

    d.dispatch('func arg1 arg2 arg3')
    d.dispatch('inst cmd1 arg1 arg2 arg3 arg4')
    d.dispatch('inst subclass subcmd arg1 arg2 arg3 arg4 arg5')
    try:
        d.dispatch('')
    except CommandNotFoundError, e:
        print 'Not found:', e
    try:
        d.dispatch('sucutrule')
    except CommandNotFoundError, e:
        print 'Not found:', e
    try:
        d.dispatch('inst cmd3')
    except CommandNotFoundError, e:
        print 'Not found:', e


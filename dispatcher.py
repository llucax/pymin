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

    command - is the command that raised the exception, expressed as a list of
              paths (or subcommands).
    """
    pass

class HandlerError(Error):
    r"""
    HandlerError(command) -> HandlerError instance :: Base handlers exception.

    All exceptions raised by the handlers should inherit from this one, so
    dispatching errors could be separated from real programming errors (bugs).
    """
    pass

class CommandNotFoundError(Error):
    r"""
    CommandNotFoundError(command) -> CommandNotFoundError instance

    This exception is raised when the command received can't be dispatched
    because there is no handlers to process it.
    """

    def __init__(self, command):
        r"""Initialize the Error object.

        See Error class documentation for more info.
        """
        self.command = command

    def __str__(self):
        return 'Command not found: "%s"' % ' '.join(self.command)

def handler(help):
    r"""handler(help) -> function wrapper :: Mark a callable as a handler.

    This is a decorator to mark a callable object as a dispatcher handler.

    help - Help string for the handler.
    """
    def wrapper(f):
        if not help:
            raise TypeError("'help' should not be empty")
        f._dispatcher_help = help
        return f
    return wrapper

def is_handler(handler):
    r"is_handler(handler) -> bool :: Tell if a object is a handler."
    return callable(handler) and hasattr(handler, '_dispatcher_help')

def get_help(handler):
    r"get_help(handler) -> unicode :: Get a handler's help string."
    if not is_handler(handler):
        raise TypeError("'%s' should be a handler" % handler.__name__)
    return handler._dispatcher_help

class Handler:
    r"""Handler() -> Handler instance :: Base class for all dispatcher handlers.

    All dispatcher handlers should inherit from this class to have some extra
    commands, like help.
    """

    @handler(u'List available commands.')
    def commands(self):
        r"""commands() -> generator :: List the available commands."""
        return (a for a in dir(self) if is_handler(getattr(self, a)))

    @handler(u'Show available commands with their help.')
    def help(self, command=None):
        r"""help([command]) -> unicode/dict :: Show help on available commands.

        If command is specified, it returns the help of that particular command.
        If not, it returns a dictionary which keys are the available commands
        and values are the help strings.
        """
        if command is None:
            return dict((a, get_help(getattr(self, a)))
                        for a in dir(self) if is_handler(getattr(self, a)))
        if not hasattr(self, command):
            raise CommandNotFoundError(command)
        handler = getattr(self, command)
        if not is_handler(handler):
            raise CommandNotFoundError(command)
        return get_help(handler)

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
        command = list()
        route = route.split() # TODO support "" and keyword arguments
        if not route:
            raise CommandNotFoundError(command)
        command.append(route[0])
        handler = self.routes.get(route[0], None)
        if handler is None:
            raise CommandNotFoundError(command)
        route = route[1:]
        while not is_handler(handler):
            if len(route) is 0:
                raise CommandNotFoundError(command)
            command.append(route[0])
            if not hasattr(handler, route[0]):
                raise CommandNotFoundError(command)
            handler = getattr(handler, route[0])
            route = route[1:]
        return handler(*route)


if __name__ == '__main__':

    @handler(u"test: Print all the arguments, return nothing.")
    def test_func(*args):
        print 'func:', args

    class TestClassSubHandler(Handler):
        @handler(u"subcmd: Print all the arguments, return nothing.")
        def subcmd(self, *args):
            print 'class.subclass.subcmd:', args

    class TestClass(Handler):
        @handler(u"cmd1: Print all the arguments, return nothing.")
        def cmd1(self, *args):
            print 'class.cmd1:', args
        @handler(u"cmd2: Print all the arguments, return nothing.")
        def cmd2(self, *args):
            print 'class.cmd2:', args
        subclass = TestClassSubHandler()

    test_class = TestClass()

    d = Dispatcher(dict(
            func=test_func,
            inst=test_class,
    ))

    d.dispatch('func arg1 arg2 arg3')
    print 'inst commands:', tuple(d.dispatch('inst commands'))
    print 'inst help:', d.dispatch('inst help')
    d.dispatch('inst cmd1 arg1 arg2 arg3 arg4')
    d.dispatch('inst cmd2 arg1 arg2')
    print 'inst subclass help:', d.dispatch('inst subclass help')
    d.dispatch('inst subclass subcmd arg1 arg2 arg3 arg4 arg5')
    try:
        d.dispatch('')
    except CommandNotFoundError, e:
        print 'Not found:', e
    try:
        d.dispatch('sucutrule piquete culete')
    except CommandNotFoundError, e:
        print 'Not found:', e
    try:
        d.dispatch('inst cmd3 arg1 arg2 arg3')
    except CommandNotFoundError, e:
        print 'Not found:', e


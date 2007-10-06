# vim: set et sts=4 sw=4 encoding=utf-8 :

r"""Command dispatcher.

This module provides a convenient and extensible command dispatching mechanism.
It's based on Zope or Cherrypy dispatching (but implemented from the scratch)
and translates commands to functions/objects/methods.
"""

__ALL__ = ('Error', 'HandlerError', 'CommandNotFoundError', 'Handler',
            'Dispatcher', 'handler', 'is_handler', 'get_help')

class Error(RuntimeError):
    r"""Error(command) -> Error instance :: Base dispatching exceptions class.

    All exceptions raised by the Dispatcher inherits from this one, so you can
    easily catch any dispatching exception.

    command - is the command that raised the exception, expressed as a list of
              paths (or subcommands).
    """

    def __init__(self, message):
        r"Initialize the Error object. See class documentation for more info."
        self.message = message

    def __unicode__(self):
        return self.message

    def __str__(self):
        return unicode(self).encode('utf-8')

class HandlerError(Error):
    r"""HandlerError(command) -> HandlerError instance :: Base handlers error.

    All exceptions raised by the handlers should inherit from this one, so
    dispatching errors could be separated from real programming errors (bugs).
    """
    pass

class CommandError(Error):
    r"""CommandError(command) -> CommandError instance :: Base command error.

    This exception is raised when there's a problem with the command itself.
    It's the base class for all command (as a string) related error.
    """

    def __init__(self, command):
        r"Initialize the object, see class documentation for more info."
        self.command = command

    def __unicode__(self):
        return u'Error in command "%s".' % u' '.join(self.command)

class CommandNotSpecifiedError(CommandError):
    r"""CommandNotSpecifiedError() -> CommandNotSpecifiedError instance.

    This exception is raised when an empty command string is received.
    """

    def __init__(self):
        r"Initialize the object, see class documentation for more info."
        pass

    def __unicode__(self):
        return u'Command not specified.'

class CommandIsAHandlerError(CommandError):
    r"""CommandIsAHandlerError() -> CommandIsAHandlerError instance.

    This exception is raised when a command is a handler containing commands
    instead of a command itself.
    """

    def __unicode__(self):
        command = ' '.join(self.command)
        return u'"%s" is a handler, not a command (type "%s help" for help).' \
                    % (command, command)

class CommandNotInHandlerError(CommandError):
    r"""CommandNotInHandlerError() -> CommandNotInHandlerError instance.

    This exception is raised when a command parent is a hanlder containing
    commands, but the command itself is not found.
    """

    def __unicode__(self):
        return u'Command "%(c)s" not found in handler "%(h)s" ' \
                u'(type "%(h)s help" for help).' \
                        % dict(c=u' '.join(self.command[-1:]),
                                h=u' '.join(self.command[0:-1]))

class CommandNotFoundError(CommandError):
    r"""CommandNotFoundError(command[, handler]) -> CommandNotFoundError object.

    This exception is raised when the command received can't be dispatched
    because there is no handlers to process it.
    """

    def __unicode__(self):
        return u'Command "%s" not found.' % u' '.join(self.command)

class ParseError(CommandError):
    r"""ParseError(command[, desc]) -> ParseError instance

    This exception is raised when there is an error parsing a command.

    command - Command that can't be parsed.

    desc - Description of the error.
    """

    def __init__(self, command, desc="can't parse"):
        r"""Initialize the object.

        See class documentation for more info.
        """
        self.command = command
        self.desc = desc

    def __unicode__(self):
        return u'Syntax error, %s: %s' % (self.desc, self.command)

class HelpNotFoundError(Error):
    r"""HelpNotFoundError(command) -> HelpNotFoundError instance.

    This exception is raised when a help command can't find the command
    asked for help.
    """

    def __init__(self, command):
        r"""Initialize the object.

        See class documentation for more info.
        """
        self.command = command

    def __unicode__(self):
        return u"Can't get help for '%s', command not found." % self.command


def handler(help):
    r"""handler(help) -> function wrapper :: Mark a callable as a handler.

    This is a decorator to mark a callable object as a dispatcher handler.

    help - Help string for the handler.
    """
    def wrapper(f):
        if not help:
            raise TypeError("'help' should not be empty")
        f._dispatcher_handler = True
        f.handler_help = help
        return f
    return wrapper

def is_handler(handler):
    r"is_handler(handler) -> bool :: Tell if a object is a handler."
    return callable(handler) and hasattr(handler, '_dispatcher_handler') \
                and handler._dispatcher_handler

class Handler:
    r"""Handler() -> Handler instance :: Base class for all dispatcher handlers.

    All dispatcher handlers should inherit from this class to have some extra
    commands, like help. You should override the 'handler_help' attribute to a
    nice help message describing the handler.
    """

    handler_help = u'Undocumented handler'

    @handler(u'List available commands')
    def commands(self):
        r"""commands() -> generator :: List the available commands."""
        return (a for a in dir(self) if is_handler(getattr(self, a)))

    @handler(u'Show available commands with their help')
    def help(self, command=None):
        r"""help([command]) -> unicode/dict :: Show help on available commands.

        If command is specified, it returns the help of that particular command.
        If not, it returns a dictionary which keys are the available commands
        and values are the help strings.
        """
        if command is None:
            d = dict()
            for a in dir(self):
                h = getattr(self, a)
                if is_handler(h) or isinstance(h, Handler):
                    d[a] = h.handler_help
            return d
        # A command was specified
        if not hasattr(self, command.encode('utf-8')):
            raise HelpNotFoundError(command)
        handler = getattr(self, command.encode('utf-8'))
        if not is_handler(handler) and not hasattr(handler):
            raise HelpNotFoundError(command)
        return handler.handler_help

def parse_command(command):
    r"""parse_command(command) -> (args, kwargs) :: Parse a command.

    This function parses a command and split it into a list of parameters. It
    has a similar to bash commandline parser. Spaces are the basic token
    separator but you can group several tokens into one by using (single or
    double) quotes. You can escape the quotes with a backslash (\' and \"),
    express a backslash literal using a double backslash (\\), use special
    meaning escaped sequences (like \a, \n, \r, \b, \v) and use unescaped
    single quotes inside a double quoted token or vice-versa. A special escape
    sequence is provided to express a NULL/None value: \N and it should appear
    always as a separated token.

    Additionally it accepts keyword arguments. When an (not-escaped) equal
    sign (=) is found, the argument is considered a keyword, and the next
    argument it's interpreted as its value.

    This function returns a tuple containing a list and a dictionary. The
    first has the positional arguments, the second, the keyword arguments.

    There is no restriction about the order, a keyword argument can be
    followed by a positional argument and vice-versa. All type of arguments
    are grouped in the list/dict returned. The order of the positional
    arguments is preserved and if there are multiple keyword arguments with
    the same key, the last value is the winner (all other values are lost).

    Examples:

    >>> parse_command('hello world')
    ([u'hello', u'world'], {})
    >>> parse_command('hello planet=earth')
    ([u'hello'], {'planet': u'earth'})
    >>> parse_command('hello planet="third rock from the sun"')
    ([u'hello'], {'planet': u'third rock from the sun'})
    >>> parse_command(u'  planet="third rock from the sun" hello ')
    ([u'hello'], {'planet': u'third rock from the sun'})
    >>> parse_command(u'  planet="third rock from the sun" "hi, hello"'
            '"how are you" ')
    ([u'hi, hello', u'how are you'], {'planet': u'third rock from the sun'})
    >>> parse_command(u'one two three "fourth number"=four')
    ([u'one', u'two', u'three'], {'fourth number': u'four'})
    >>> parse_command(u'one two three "fourth number=four"')
    ([u'one', u'two', u'three', u'fourth number=four'], {})
    >>> parse_command(u'one two three fourth\=four')
    ([u'one', u'two', u'three', u'fourth=four'], {})
    >>> parse_command(u'one two three fourth=four=five')
    ([u'one', u'two', u'three'], {'fourth': u'four=five'})
    >>> parse_command(ur'nice\nlong\n\ttext')
    ([u'nice\nlong\n\ttext'], {})
    >>> parse_command('=hello')
    ([u'=hello'], {})
    >>> parse_command(r'\thello')
    ([u'\thello'], {})
    >>> parse_command(r'\N')
    ([None], {})
    >>> parse_command(r'none=\N')
    ([], {'none': None})
    >>> parse_command(r'\N=none')
    ([], {'\\N': 'none'})
    >>> parse_command(r'Not\N')
    ([u'Not\\N'], {})
    >>> parse_command(r'\None')
    ([u'\\None'], {})

    This examples are syntax errors:
    Missing quote: "hello world
    Missing value: hello=
    """
    SEP, TOKEN, DQUOTE, SQUOTE, EQUAL = u' ', None, u'"', u"'", u'=' # states
    separators = (u' ', u'\t', u'\v', u'\n') # token separators
    escaped_chars = (u'a', u'n', u'r', u'b', u'v', u't') # escaped sequences
    seq = []
    dic = {}
    buff = u''
    escape = False
    keyword = None
    state = SEP
    for n, c in enumerate(command):
        # Escaped character
        if escape:
            for e in escaped_chars:
                if c == e:
                    buff += eval(u'"\\' + e + u'"')
                    break
            else:
                if c == 'N':
                    buff += r'\N'
                else:
                    buff += c
            escape = False
            continue
        # Escaped sequence start
        if c == u'\\':
            escape = True
            continue
        # Looking for spaces
        if state == SEP:
            if c in separators:
                continue
            if buff and n != 2: # Not the first item (even if was a escape seq)
                if c == EQUAL: # Keyword found
                    keyword = buff
                    buff = u''
                    continue
                if buff == r'\N':
                    buff = None
                if keyword is not None: # Value found
                    dic[str(keyword)] = buff
                    keyword = None
                else: # Normal parameter found
                    seq.append(buff)
                buff = u''
            state = TOKEN
        # Getting a token
        if state == TOKEN:
            if c == DQUOTE:
                state = DQUOTE
                continue
            if c == SQUOTE:
                state = SQUOTE
                continue
            # Check if a keyword is added
            if c == EQUAL and keyword is None and buff:
                keyword = buff
                buff = u''
                state = SEP
                continue
            if c in separators:
                state = SEP
                continue
            buff += c
            continue
        # Inside a double quote
        if state == DQUOTE:
            if c == DQUOTE:
                state = TOKEN
                continue
            buff += c
            continue
        # Inside a single quote
        if state == SQUOTE:
            if c == SQUOTE:
                state = TOKEN
                continue
            buff += c
            continue
        assert 0, u'Unexpected state'
    if state == DQUOTE or state == SQUOTE:
        raise ParseError(command, u'missing closing quote (%s)' % state)
    if not buff and keyword is not None:
        raise ParseError(command,
                        u'keyword argument (%s) without value' % keyword)
    if buff:
        if buff == r'\N':
            buff = None
        if keyword is not None:
            dic[str(keyword)] = buff
        else:
            seq.append(buff)
    return (seq, dic)

class Dispatcher:
    r"""Dispatcher([root]) -> Dispatcher instance :: Command dispatcher.

    This class provides a modular and extensible dispatching mechanism. You
    specify a root handler (probably as a pymin.dispatcher.Handler subclass),

    The command can have arguments, separated by (any number of) spaces and
    keyword arguments (see parse_command for more details).

    The dispatcher tries to route the command as deeply as it can, passing
    the other "path" components as arguments to the callable. To route the
    command it inspects the callable attributes to find a suitable callable
    attribute to handle the command in a more specific way, and so on.

    Example:
    >>> d = Dispatcher(dict(handler=some_handler))
    >>> d.dispatch('handler attribute method arg1 "arg 2" arg=3')

    If 'some_handler' is an object with an 'attribute' that is another
    object which has a method named 'method', then
    some_handler.attribute.method('arg1', 'arg 2', arg=3) will be called.
    If some_handler is a function, then some_handler('attribute', 'method',
    'arg1', 'arg 2', arg=3) will be called. The handler "tree" can be as
    complex and deep as you want.

    If some command can't be dispatched, a CommandError subclass is raised.
    """

    def __init__(self, root):
        r"""Initialize the Dispatcher object.

        See Dispatcher class documentation for more info.
        """
        self.root = root

    def dispatch(self, route):
        r"""dispatch(route) -> None :: Dispatch a command string.

        This method searches for a suitable callable object in the routes
        "tree" and call it, or raises a CommandError subclass if the command
        can't be dispatched.

        route - *unicode* string with the command route.
        """
        command = list()
        (route, kwargs) = parse_command(route)
        if not route:
            raise CommandNotSpecifiedError()
        handler = self.root
        while not is_handler(handler):
            if len(route) is 0:
                if isinstance(handler, Handler):
                    raise CommandIsAHandlerError(command)
                raise CommandNotFoundError(command)
            command.append(route[0])
            if not hasattr(handler, route[0].encode('utf-8')):
                if isinstance(handler, Handler) and len(command) > 1:
                    raise CommandNotInHandlerError(command)
                raise CommandNotFoundError(command)
            handler = getattr(handler, route[0].encode('utf-8'))
            route = route[1:]
        return handler(*route, **kwargs)


if __name__ == '__main__':

    @handler(u"test: Print all the arguments, return nothing")
    def test_func(*args):
        print 'func:', args

    class TestClassSubHandler(Handler):
        @handler(u"subcmd: Print all the arguments, return nothing")
        def subcmd(self, *args):
            print 'class.subclass.subcmd:', args

    class TestClass(Handler):
        @handler(u"cmd1: Print all the arguments, return nothing")
        def cmd1(self, *args):
            print 'class.cmd1:', args
        @handler(u"cmd2: Print all the arguments, return nothing")
        def cmd2(self, *args):
            print 'class.cmd2:', args
        subclass = TestClassSubHandler()

    class RootHandler(Handler):
        func = staticmethod(test_func)
        inst = TestClass()

    d = Dispatcher(RootHandler())

    d.dispatch(r'''func arg1 arg2 arg3 "fourth 'argument' with \", a\ttab and\n\\n"''')
    print 'inst commands:', tuple(d.dispatch('inst commands'))
    print 'inst help:', d.dispatch('inst help')
    d.dispatch('inst cmd1 arg1 arg2 arg3 arg4')
    d.dispatch('inst cmd2 arg1 arg2')
    print 'inst subclass help:', d.dispatch('inst subclass help')
    d.dispatch('inst subclass subcmd arg1 arg2 arg3 arg4 arg5')
    try:
        d.dispatch('')
    except CommandNotSpecifiedError, e:
        print 'Not found:', e
    try:
        d.dispatch('sucutrule piquete culete')
    except CommandNotFoundError, e:
        print 'Not found:', e
    try:
        d.dispatch('inst cmd3 arg1 arg2 arg3')
    except CommandNotInHandlerError, e:
        print 'Not found:', e
    try:
        d.dispatch('inst')
    except CommandIsAHandlerError, e:
        print 'Not found:', e
    print
    print

    # Parser tests
    p = parse_command('hello world')
    assert p == ([u'hello', u'world'], {}), p
    p = parse_command('hello planet=earth')
    assert p  == ([u'hello'], {'planet': u'earth'}), p
    p = parse_command('hello planet="third rock from the sun"')
    assert p == ([u'hello'], {'planet': u'third rock from the sun'}), p
    p = parse_command(u'  planet="third rock from the sun" hello ')
    assert p == ([u'hello'], {'planet': u'third rock from the sun'}), p
    p = parse_command(u'  planet="third rock from the sun" "hi, hello" '
                            '"how are you" ')
    assert p == ([u'hi, hello', u'how are you'],
                {'planet': u'third rock from the sun'}), p
    p = parse_command(u'one two three "fourth number"=four')
    assert p == ([u'one', u'two', u'three'], {'fourth number': u'four'}), p
    p = parse_command(u'one two three "fourth number=four"')
    assert p == ([u'one', u'two', u'three', u'fourth number=four'], {}), p
    p = parse_command(u'one two three fourth\=four')
    assert p == ([u'one', u'two', u'three', u'fourth=four'], {}), p
    p = parse_command(u'one two three fourth=four=five')
    assert p == ([u'one', u'two', u'three'], {'fourth': u'four=five'}), p
    p = parse_command(ur'nice\nlong\n\ttext')
    assert p == ([u'nice\nlong\n\ttext'], {}), p
    p = parse_command('=hello')
    assert p == ([u'=hello'], {}), p
    p = parse_command(r'\thello')
    assert p == ([u'\thello'], {}), p
    p = parse_command(r'\N')
    assert p == ([None], {}), p
    p = parse_command(r'none=\N')
    assert p == ([], {'none': None}), p
    p = parse_command(r'\N=none')
    assert p == ([], {'\\N': 'none'}), p
    p = parse_command(r'Not\N')
    assert p == ([u'Not\\N'], {}), p
    p = parse_command(r'\None')
    assert p == ([u'\\None'], {}), p
    try:
        p = parse_command('hello=')
    except ParseError, e:
        pass
    else:
        assert False, p + ' should raised a ParseError'
    try:
        p = parse_command('"hello')
    except ParseError, e:
        pass
    else:
        assert False, p + ' should raised a ParseError'


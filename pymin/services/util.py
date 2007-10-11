# vim: set encoding=utf-8 et sw=4 sts=4 :

import subprocess
from mako.template import Template
from mako.runtime import Context
from os import path
try:
    import cPickle as pickle
except ImportError:
    import pickle

from pymin.dispatcher import Handler, handler, HandlerError, \
                                CommandNotFoundError

#DEBUG = False
DEBUG = True

__ALL__ = ('ServiceHandler', 'InitdHandler', 'SubHandler', 'DictSubHandler',
            'ListSubHandler', 'Persistent', 'ConfigWriter', 'Error',
            'ReturnNot0Error', 'ExecutionError', 'ItemError',
            'ItemAlreadyExistsError', 'ItemNotFoundError', 'call')

class Error(HandlerError):
    r"""
    Error(message) -> Error instance :: Base ServiceHandler exception class.

    All exceptions raised by the ServiceHandler inherits from this one, so
    you can easily catch any ServiceHandler exception.

    message - A descriptive error message.
    """
    pass

class ReturnNot0Error(Error):
    r"""
    ReturnNot0Error(return_value) -> ReturnNot0Error instance.

    A command didn't returned the expected 0 return value.

    return_value - Return value returned by the command.
    """

    def __init__(self, return_value):
        r"Initialize the object. See class documentation for more info."
        self.return_value = return_value

    def __unicode__(self):
        return 'The command returned %d' % self.return_value

class ExecutionError(Error):
    r"""
    ExecutionError(command, error) -> ExecutionError instance.

    Error executing a command.

    command - Command that was tried to execute.

    error - Error received when trying to execute the command.
    """

    def __init__(self, command, error):
        r"Initialize the object. See class documentation for more info."
        self.command = command
        self.error = error

    def __unicode__(self):
        command = self.command
        if not isinstance(self.command, basestring):
            command = ' '.join(command)
        return "Can't execute command %s: %s" % (command, self.error)

class ParameterError(Error, KeyError):
    r"""
    ParameterError(paramname) -> ParameterError instance

    This is the base exception for all DhcpHandler parameters related errors.
    """

    def __init__(self, paramname):
        r"Initialize the object. See class documentation for more info."
        self.message = 'Parameter error: "%s"' % paramname

class ParameterNotFoundError(ParameterError):
    r"""
    ParameterNotFoundError(paramname) -> ParameterNotFoundError instance

    This exception is raised when trying to operate on a parameter that doesn't
    exists.
    """

    def __init__(self, paramname):
        r"Initialize the object. See class documentation for more info."
        self.message = 'Parameter not found: "%s"' % paramname

class ItemError(Error, KeyError):
    r"""
    ItemError(key) -> ItemError instance.

    This is the base exception for all item related errors.
    """

    def __init__(self, key):
        r"Initialize the object. See class documentation for more info."
        self.message = u'Item error: "%s"' % key

class ItemAlreadyExistsError(ItemError):
    r"""
    ItemAlreadyExistsError(key) -> ItemAlreadyExistsError instance.

    This exception is raised when trying to add an item that already exists.
    """

    def __init__(self, key):
        r"Initialize the object. See class documentation for more info."
        self.message = u'Item already exists: "%s"' % key

class ItemNotFoundError(ItemError):
    r"""
    ItemNotFoundError(key) -> ItemNotFoundError instance

    This exception is raised when trying to operate on an item that doesn't
    exists.
    """

    def __init__(self, key):
        r"Initialize the object. See class documentation for more info."
        self.message = u'Item not found: "%s"' % key


def call(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, close_fds=True, universal_newlines=True,
            **kw):
    if DEBUG:
        if not isinstance(command, basestring):
            command = ' '.join(command)
        print 'Executing command:', command
        return
    try:
        r = subprocess.call(command, stdin=stdin, stdout=stdout, stderr=stderr,
                                universal_newlines=universal_newlines,
                                close_fds=close_fds, **kw)
    except Exception, e:
        raise ExecutionError(command, e)
    if r is not 0:
        raise ExecutionError(command, ReturnNot0Error(r))

class Persistent:
    r"""Persistent([attrs[, dir[, ext]]]) -> Persistent.

    This is a helper class to inherit from to automatically handle data
    persistence using pickle.

    The variables attributes to persist (attrs), and the pickle directory (dir)
    and file extension (ext) can be defined by calling the constructor or in a
    more declarative way as class attributes, like:

    class TestHandler(Persistent):
        _persistent_attrs = ('some_attr', 'other_attr')
        _persistent_dir = 'persistent-data'
        _persistent_ext = '.pickle'

    The default dir is '.' and the default extension is '.pkl'. There are no
    default variables, and they should be specified as string if a single
    attribute should be persistent or as a tuple of strings if they are more.
    The strings should be the attribute names to be persisted. For each
    attribute a separated pickle file is generated in the pickle directory.

    You can call _dump() and _load() to write and read the data respectively.
    """
    # TODO implement it using metaclasses to add the handlers method by demand
    # (only for specifieds commands).

    _persistent_attrs = ()
    _persistent_dir = '.'
    _persistent_ext = '.pkl'

    def __init__(self, attrs=None, dir=None, ext=None):
        r"Initialize the object, see the class documentation for details."
        if attrs is not None:
            self._persistent_attrs = attrs
        if dir is not None:
            self._persistent_dir = dir
        if ext is not None:
            self._persistent_ext = ext

    def _dump(self):
        r"_dump() -> None :: Dump all persistent data to pickle files."
        if isinstance(self._persistent_attrs, basestring):
            self._persistent_attrs = (self._persistent_attrs,)
        for attrname in self._persistent_attrs:
            self._dump_attr(attrname)

    def _load(self):
        r"_load() -> None :: Load all persistent data from pickle files."
        if isinstance(self._persistent_attrs, basestring):
            self._persistent_attrs = (self._persistent_attrs,)
        for attrname in self._persistent_attrs:
            self._load_attr(attrname)

    def _dump_attr(self, attrname):
        r"_dump_attr() -> None :: Dump a specific variable to a pickle file."
        f = file(self._pickle_filename(attrname), 'wb')
        pickle.dump(getattr(self, attrname), f, 2)
        f.close()

    def _load_attr(self, attrname):
        r"_load_attr() -> object :: Load a specific pickle file."
        f = file(self._pickle_filename(attrname))
        setattr(self, attrname, pickle.load(f))
        f.close()

    def _pickle_filename(self, name):
        r"_pickle_filename() -> string :: Construct a pickle filename."
        return path.join(self._persistent_dir, name) + self._persistent_ext

class Restorable(Persistent):
    r"""Restorable([defaults]) -> Restorable.

    This is a helper class to inherit from that provides a nice _restore()
    method to restore the persistent data if any, or load some nice defaults
    if not.

    The defaults can be defined by calling the constructor or in a more
    declarative way as class attributes, like:

    class TestHandler(Restorable):
        _persistent_attrs = ('some_attr', 'other_attr')
        _restorable_defaults = dict(
                some_attr = 'some_default',
                other_attr = 'other_default')

    The defaults is a dictionary, very coupled with the _persistent_attrs
    attribute inherited from Persistent. The defaults keys should be the
    values from _persistent_attrs, and the values the default values.

    The _restore() method returns True if the data was restored successfully
    or False if the defaults were loaded (in case you want to take further
    actions). If a _write_config method if found, it's executed when a restore
    fails too.
    """
    # TODO implement it using metaclasses to add the handlers method by demand
    # (only for specifieds commands).

    _restorable_defaults = dict()

    def __init__(self, defaults=None):
        r"Initialize the object, see the class documentation for details."
        if defaults is not None:
            self._restorable_defaults = defaults

    def _restore(self):
        r"_restore() -> bool :: Restore persistent data or create a default."
        try:
            self._load()
            # TODO tener en cuenta servicios que hay que levantar y los que no
            if hasattr(self, 'commit'): # TODO deberia ser reload y/o algo para comandos
                self.commit()
            return True
        except IOError:
            for (k, v) in self._restorable_defaults.items():
                setattr(self, k, v)
            # TODO tener en cuenta servicios que hay que levantar y los que no
            if hasattr(self, 'commit'):
                self.commit()
                return False
            self._dump()
            if hasattr(self, '_write_config'):
                self._write_config()
            if hasattr(self, 'reload'):
                self.reload()
            return False

class ConfigWriter:
    r"""ConfigWriter([initd_name[, initd_dir]]) -> ConfigWriter.

    This is a helper class to inherit from to automatically handle
    configuration generation. Mako template system is used for configuration
    files generation.

    The configuration filenames, the generated configuration files directory
    and the templates directory can be defined by calling the constructor or
    in a more declarative way as class attributes, like:

    class TestHandler(ConfigWriter):
        _config_writer_files = ('base.conf', 'custom.conf')
        _config_writer_cfg_dir = {
                                    'base.conf': '/etc/service',
                                    'custom.conf': '/etc/service/conf.d',
                                 }
        _config_writer_tpl_dir = 'templates'

    The generated configuration files directory defaults to '.' and the
    templates directory to 'templates'. _config_writer_files has no default and
    must be specified in either way. It can be string or a tuple if more than
    one configuration file must be generated. _config_writer_cfg_dir could be a
    dict mapping which file should be stored in which directory, or a single
    string if all the config files should go to the same directory.

    The template filename and the generated configuration filename are both the
    same (so if you want to generate some /etc/config, you should have some
    templates/config template). That's why _config_writer_cfg_dir and
    _config_writer_tpl_dir can't be the same. This is not true for very
    specific cases where _write_single_config() is used.

    When you write your Handler, you should call _config_build_templates() in
    you Handler constructor to build the templates.

    To write the configuration files, you must use the _write_config() method.
    To know what variables to replace in the template, you have to provide a
    method called _get_config_vars(tamplate_name), which should return a
    dictionary of variables to pass to the template system to be replaced in
    the template for the configuration file 'config_file'.
    """
    # TODO implement it using metaclasses to add the handlers method by demand
    # (only for specifieds commands).

    _config_writer_files = ()
    _config_writer_cfg_dir = '.'
    _config_writer_tpl_dir = 'templates'

    def __init__(self, files=None, cfg_dir=None, tpl_dir=None):
        r"Initialize the object, see the class documentation for details."
        if files is not None:
            self._config_writer_files = files
        if cfg_dir is not None:
            self._config_writer_cfg_dir = cfg_dir
        if tpl_dir is not None:
            self._config_writer_tpl_dir = tpl_dir
        self._config_build_templates()

    def _config_build_templates(self):
        r"_config_writer_templates() -> None :: Build the template objects."
        if isinstance(self._config_writer_files, basestring):
            self._config_writer_files = (self._config_writer_files,)
        if not hasattr(self, '_config_writer_templates') \
                                        or not self._config_writer_templates:
            self._config_writer_templates = dict()
            for t in self._config_writer_files:
                f = path.join(self._config_writer_tpl_dir, t)
                self._config_writer_templates[t] = Template(filename=f)

    def _render_config(self, template_name, vars=None):
        r"""_render_config(template_name[, config_filename[, vars]]).

        Render a single config file using the template 'template_name'. If
        vars is specified, it's used as the dictionary with the variables
        to replace in the templates, if not, it looks for a
        _get_config_vars() method to get it.
        """
        if vars is None:
            if hasattr(self, '_get_config_vars'):
                vars = self._get_config_vars(template_name)
            else:
                vars = dict()
        elif callable(vars):
            vars = vars(template_name)
        return self._config_writer_templates[template_name].render(**vars)

    def _get_config_path(self, template_name, config_filename=None):
        r"Get a complete configuration path."
        if not config_filename:
            config_filename = template_name
        if isinstance(self._config_writer_cfg_dir, basestring):
            return path.join(self._config_writer_cfg_dir, config_filename)
        return path.join(self._config_writer_cfg_dir[template_name],
                            config_filename)

    def _write_single_config(self, template_name, config_filename=None, vars=None):
        r"""_write_single_config(template_name[, config_filename[, vars]]).

        Write a single config file using the template 'template_name'. If no
        config_filename is specified, the config filename will be the same as
        the 'template_name' (but stored in the generated config files
        directory). If it's specified, the generated config file is stored in
        the file called 'config_filename' (also in the generated files
        directory). If vars is specified, it's used as the dictionary with the
        variables to replace in the templates, if not, it looks for a
        _get_config_vars() method to get it.
        """
        if vars is None:
            if hasattr(self, '_get_config_vars'):
                vars = self._get_config_vars(template_name)
            else:
                vars = dict()
        elif callable(vars):
            vars = vars(template_name)
        f = file(self._get_config_path(template_name, config_filename), 'w')
        ctx = Context(f, **vars)
        self._config_writer_templates[template_name].render_context(ctx)
        f.close()

    def _write_config(self):
        r"_write_config() -> None :: Generate all the configuration files."
        for t in self._config_writer_files:
            self._write_single_config(t)


class ServiceHandler(Handler):
    r"""ServiceHandler([start[, stop[, restart[, reload]]]]) -> ServiceHandler.

    This is a helper class to inherit from to automatically handle services
    with start, stop, restart, reload actions.

    The actions can be defined by calling the constructor with all the
    parameters or in a more declarative way as class attributes, like:

    class TestHandler(ServiceHandler):
        _service_start = ('command', 'start')
        _service_stop = ('command', 'stop')
        _service_restart = ('command', 'restart')
        _service_reload = 'reload-command'

    Commands are executed without using the shell, that's why they are specified
    as tuples (where the first element is the command and the others are the
    command arguments). If only a command is needed (without arguments) a single
    string can be specified.

    All commands must be specified.
    """
    # TODO implement it using metaclasses to add the handlers method by demand
    # (only for specifieds commands).

    def __init__(self, start=None, stop=None, restart=None, reload=None):
        r"Initialize the object, see the class documentation for details."
        for (name, action) in dict(start=start, stop=stop, restart=restart,
                                                    reload=reload).items():
            if action is not None:
                setattr(self, '_service_%s' % name, action)

    @handler(u'Start the service.')
    def start(self):
        r"start() -> None :: Start the service."
        call(self._service_start)

    @handler(u'Stop the service.')
    def stop(self):
        r"stop() -> None :: Stop the service."
        call(self._service_stop)

    @handler(u'Restart the service.')
    def restart(self):
        r"restart() -> None :: Restart the service."
        call(self._service_restart)

    @handler(u'Reload the service config (without restarting, if possible).')
    def reload(self):
        r"reload() -> None :: Reload the configuration of the service."
        call(self._service_reload)

class InitdHandler(Handler):
    r"""InitdHandler([initd_name[, initd_dir]]) -> InitdHandler.

    This is a helper class to inherit from to automatically handle services
    with start, stop, restart, reload actions using a /etc/init.d like script.

    The name and directory of the script can be defined by calling the
    constructor or in a more declarative way as class attributes, like:

    class TestHandler(ServiceHandler):
        _initd_name = 'some-service'
        _initd_dir = '/usr/local/etc/init.d'

    The default _initd_dir is '/etc/init.d', _initd_name has no default and
    must be specified in either way.

    Commands are executed without using the shell.
    """
    # TODO implement it using metaclasses to add the handlers method by demand
    # (only for specifieds commands).

    _initd_dir = '/etc/init.d'

    def __init__(self, initd_name=None, initd_dir=None):
        r"Initialize the object, see the class documentation for details."
        if initd_name is not None:
            self._initd_name = initd_name
        if initd_dir is not None:
            self._initd_dir = initd_dir

    @handler(u'Start the service.')
    def start(self):
        r"start() -> None :: Start the service."
        call((path.join(self._initd_dir, self._initd_name), 'start'))

    @handler(u'Stop the service.')
    def stop(self):
        r"stop() -> None :: Stop the service."
        call((path.join(self._initd_dir, self._initd_name), 'stop'))

    @handler(u'Restart the service.')
    def restart(self):
        r"restart() -> None :: Restart the service."
        call((path.join(self._initd_dir, self._initd_name), 'restart'))

    @handler(u'Reload the service config (without restarting, if possible).')
    def reload(self):
        r"reload() -> None :: Reload the configuration of the service."
        call((path.join(self._initd_dir, self._initd_name), 'reload'))

class TransactionalHandler(Handler):
    r"""Handle command transactions providing a commit and rollback commands.

    This is a helper class to inherit from to automatically handle
    transactional handlers, which have commit and rollback commands.

    The handler should provide a reload() method (see ServiceHandler and
    InitdHandler for helper classes to provide this) which will be called
    when a commit command is issued (if a reload() command is present).
    The persistent data will be written too (if a _dump() method is provided,
    see Persistent and Restorable for that), and the configuration files
    will be generated (if a _write_config method is present, see ConfigWriter).
    """
    # TODO implement it using metaclasses to add the handlers method by demand
    # (only for specifieds commands).

    @handler(u'Commit the changes (reloading the service, if necessary).')
    def commit(self):
        r"commit() -> None :: Commit the changes and reload the service."
        if hasattr(self, '_dump'):
            self._dump()
        if hasattr(self, '_write_config'):
            self._write_config()
        if hasattr(self, 'reload'):
            self.reload()

    @handler(u'Discard all the uncommited changes.')
    def rollback(self):
        r"rollback() -> None :: Discard the changes not yet commited."
        if hasattr(self, '_load'):
            self._load()

class ParametersHandler(Handler):
    r"""ParametersHandler([attr]) -> ParametersHandler.

    This is a helper class to inherit from to automatically handle
    service parameters, providing set, get, list and show commands.

    The attribute that holds the parameters can be defined by calling the
    constructor or in a more declarative way as class attributes, like:

    class TestHandler(ServiceHandler):
        _parameters_attr = 'some_attr'

    The default is 'params' and it should be a dictionary.
    """
    # TODO implement it using metaclasses to add the handlers method by demand
    # (only for specifieds commands).

    _parameters_attr = 'params'

    def __init__(self, attr=None):
        r"Initialize the object, see the class documentation for details."
        if attr is not None:
            self._parameters_attr = attr

    @handler(u'Set a service parameter.')
    def set(self, param, value):
        r"set(param, value) -> None :: Set a service parameter."
        if not param in self.params:
            raise ParameterNotFoundError(param)
        self.params[param] = value

    @handler(u'Get a service parameter.')
    def get(self, param):
        r"get(param) -> None :: Get a service parameter."
        if not param in self.params:
            raise ParameterNotFoundError(param)
        return self.params[param]

    @handler(u'List all available service parameters.')
    def list(self):
        r"list() -> tuple :: List all the parameter names."
        return self.params.keys()

    @handler(u'Get all service parameters, with their values.')
    def show(self):
        r"show() -> (key, value) tuples :: List all the parameters."
        return self.params.items()

class SubHandler(Handler):
    r"""SubHandler(parent) -> SubHandler instance :: Handles subcommands.

    This is a helper class to build sub handlers that needs to reference the
    parent handler.

    parent - Parent Handler object.
    """

    def __init__(self, parent):
        r"Initialize the object, see the class documentation for details."
        self.parent = parent

class ListSubHandler(SubHandler):
    r"""ListSubHandler(parent) -> ListSubHandler instance.

    This is a helper class to inherit from to automatically handle subcommands
    that operates over a list parent attribute.

    The list attribute to handle and the class of objects that it contains can
    be defined by calling the constructor or in a more declarative way as
    class attributes, like:

    class TestHandler(ListSubHandler):
        _list_subhandler_attr = 'some_list'
        _list_subhandler_class = SomeClass

    This way, the parent's some_list attribute (self.parent.some_list) will be
    managed automatically, providing the commands: add, update, delete, get,
    list and show. New items will be instances of SomeClass, which should
    provide a cmp operator to see if the item is on the list and an update()
    method, if it should be possible to modify it.
    """

    def __init__(self, parent, attr=None, cls=None):
        r"Initialize the object, see the class documentation for details."
        self.parent = parent
        if attr is not None:
            self._list_subhandler_attr = attr
        if cls is not None:
            self._list_subhandler_class = cls

    def _list(self):
        return getattr(self.parent, self._list_subhandler_attr)

    @handler(u'Add a new item')
    def add(self, *args, **kwargs):
        r"add(...) -> None :: Add an item to the list."
        item = self._list_subhandler_class(*args, **kwargs)
        if item in self._list():
            raise ItemAlreadyExistsError(item)
        self._list().append(item)

    @handler(u'Update an item')
    def update(self, index, *args, **kwargs):
        r"update(index, ...) -> None :: Update an item of the list."
        # TODO make it right with metaclasses, so the method is not created
        # unless the update() method really exists.
        # TODO check if the modified item is the same of an existing one
        index = int(index) # TODO validation
        if not hasattr(self._list_subhandler_class, 'update'):
            raise CommandNotFoundError(('update',))
        try:
            self._list()[index].update(*args, **kwargs)
        except IndexError:
            raise ItemNotFoundError(index)

    @handler(u'Delete an item')
    def delete(self, index):
        r"delete(index) -> None :: Delete an item of the list."
        index = int(index) # TODO validation
        try:
            return self._list().pop(index)
        except IndexError:
            raise ItemNotFoundError(index)

    @handler(u'Get information about an item')
    def get(self, index):
        r"get(index) -> Host :: List all the information of an item."
        index = int(index) # TODO validation
        try:
            return self._list()[index]
        except IndexError:
            raise ItemNotFoundError(index)

    @handler(u'Get how many items are in the list')
    def len(self):
        r"len() -> int :: Get how many items are in the list."
        return len(self._list())

    @handler(u'Get information about all items')
    def show(self):
        r"show() -> list of Hosts :: List all the complete items information."
        return self._list()

class DictSubHandler(SubHandler):
    r"""DictSubHandler(parent) -> DictSubHandler instance.

    This is a helper class to inherit from to automatically handle subcommands
    that operates over a dict parent attribute.

    The dict attribute to handle and the class of objects that it contains can
    be defined by calling the constructor or in a more declarative way as
    class attributes, like:

    class TestHandler(DictSubHandler):
        _dict_subhandler_attr = 'some_dict'
        _dict_subhandler_class = SomeClass

    This way, the parent's some_dict attribute (self.parent.some_dict) will be
    managed automatically, providing the commands: add, update, delete, get,
    list and show. New items will be instances of SomeClass, which should
    provide a constructor with at least the key value and an update() method,
    if it should be possible to modify it.
    """

    def __init__(self, parent, attr=None, cls=None):
        r"Initialize the object, see the class documentation for details."
        self.parent = parent
        if attr is not None:
            self._dict_subhandler_attr = attr
        if cls is not None:
            self._dict_subhandler_class = cls

    def _dict(self):
        return getattr(self.parent, self._dict_subhandler_attr)

    @handler(u'Add a new item')
    def add(self, key, *args, **kwargs):
        r"add(key, ...) -> None :: Add an item to the dict."
        item = self._dict_subhandler_class(key, *args, **kwargs)
        if key in self._dict():
            raise ItemAlreadyExistsError(key)
        self._dict()[key] = item

    @handler(u'Update an item')
    def update(self, key, *args, **kwargs):
        r"update(key, ...) -> None :: Update an item of the dict."
        # TODO make it right with metaclasses, so the method is not created
        # unless the update() method really exists.
        if not hasattr(self._dict_subhandler_class, 'update'):
            raise CommandNotFoundError(('update',))
        if not key in self._dict():
            raise ItemNotFoundError(key)
        self._dict()[key].update(*args, **kwargs)

    @handler(u'Delete an item')
    def delete(self, key):
        r"delete(key) -> None :: Delete an item of the dict."
        if not key in self._dict():
            raise ItemNotFoundError(key)
        del self._dict()[key]

    @handler(u'Get information about an item')
    def get(self, key):
        r"get(key) -> Host :: List all the information of an item."
        if not key in self._dict():
            raise ItemNotFoundError(key)
        return self._dict()[key]

    @handler(u'List all the items by key')
    def list(self):
        r"list() -> tuple :: List all the item keys."
        return self._dict().keys()

    @handler(u'Get information about all items')
    def show(self):
        r"show() -> list of Hosts :: List all the complete items information."
        return self._dict().values()


if __name__ == '__main__':

    # Execution tests
    class STestHandler1(ServiceHandler):
        _service_start = ('service', 'start')
        _service_stop = ('service', 'stop')
        _service_restart = ('ls', '/')
        _service_reload = ('cp', '/la')
    class STestHandler2(ServiceHandler):
        def __init__(self):
            ServiceHandler.__init__(self, 'cmd-start', 'cmd-stop',
                                        'cmd-restart', 'cmd-reload')
    class ITestHandler1(InitdHandler):
        _initd_name = 'test1'
    class ITestHandler2(InitdHandler):
        def __init__(self):
            InitdHandler.__init__(self, 'test2', '/usr/local/etc/init.d')
    handlers = [
        STestHandler1(),
        STestHandler2(),
        ITestHandler1(),
        ITestHandler2(),
    ]
    for h in handlers:
        print h.__class__.__name__
        try:
            h.start()
        except ExecutionError, e:
            print e
        try:
            h.stop()
        except ExecutionError, e:
            print e
        try:
            h.restart()
        except ExecutionError, e:
            print e
        try:
            h.reload()
        except ExecutionError, e:
            print e
        print

    # Persistent test
    print 'PTestHandler'
    class PTestHandler(Persistent):
        _persistent_attrs = 'vars'
        def __init__(self):
            self.vars = dict(a=1, b=2)
    h = PTestHandler()
    print h.vars
    h._dump()
    h.vars['x'] = 100
    print h.vars
    h._load()
    print h.vars
    h.vars['x'] = 100
    h._dump()
    print h.vars
    del h.vars['x']
    print h.vars
    h._load()
    print h.vars
    print

    # Restorable test
    print 'RTestHandler'
    class RTestHandler(Restorable):
        _persistent_attrs = 'vars'
        _restorable_defaults = dict(vars=dict(a=1, b=2))
        def __init__(self):
            self._restore()
    h = RTestHandler()
    print h.vars
    h.vars['x'] = 100
    h._dump()
    h = RTestHandler()
    print h.vars
    print

    # ConfigWriter test
    print 'CTestHandler'
    import os
    os.mkdir('templates')
    f = file('templates/config', 'w')
    f.write('Hello, ${name}! You are ${what}.')
    f.close()
    print 'template:'
    print file('templates/config').read()
    class CTestHandler(ConfigWriter):
        _config_writer_files = 'config'
        def __init__(self):
            self._config_build_templates()
        def _get_config_vars(self, config_file):
            return dict(name='you', what='a parrot')
    h = CTestHandler()
    h._write_config()
    print 'config:'
    print file('config').read()
    os.unlink('config')
    os.unlink('templates/config')
    os.rmdir('templates')
    print


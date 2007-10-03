# vim: set encoding=utf-8 et sw=4 sts=4 :

import subprocess
from mako.template import Template
from mako.runtime import Context
from os import path
try:
    import cPickle as pickle
except ImportError:
    import pickle

from dispatcher import Handler, handler, HandlerError

#DEBUG = False
DEBUG = True

__ALL__ = ('ServiceHandler', 'InitdHandler', 'Persistent', 'ConfigWriter',
            'Error', 'ReturnNot0Error', 'ExecutionError', 'call')

class Error(HandlerError):
    r"""
    Error(message) -> Error instance :: Base ServiceHandler exception class.

    All exceptions raised by the ServiceHandler inherits from this one, so
    you can easily catch any ServiceHandler exception.

    message - A descriptive error message.
    """

    def __init__(self, message):
        r"Initialize the object. See class documentation for more info."
        self.message = message

    def __str__(self):
        return self.message

class ReturnNot0Error(Error):
    r"""
    ReturnNot0Error(return_value) -> ReturnNot0Error instance.

    A command didn't returned the expected 0 return value.

    return_value - Return value returned by the command.
    """

    def __init__(self, return_value):
        r"Initialize the object. See class documentation for more info."
        self.return_value = return_value

    def __str__(self):
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

    def __str__(self):
        command = self.command
        if not isinstance(self.command, basestring):
            command = ' '.join(command)
        return "Can't execute command %s: %s" % (command, self.error)

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

class Persistent:
    r"""Persistent([vars[, dir[, ext]]]) -> Persistent.

    This is a helper class to inherit from to automatically handle data
    persistence using pickle.

    The variables attributes to persist (vars), and the pickle directory (dir)
    and file extension (ext) can be defined by calling the constructor or in a
    more declarative way as class attributes, like:

    class TestHandler(Persistent):
        _persistent_vars = ('some_var', 'other_var')
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

    _persistent_vars = ()
    _persistent_dir = '.'
    _persistent_ext = '.pkl'

    def __init__(self, vars=None, dir=None, ext=None):
        r"Initialize the object, see the class documentation for details."
        if vars is not None:
            self._persistent_vars = vars
        if dir is not None:
            self._persistent_dir = dir
        if ext is not None:
            self._persistent_ext = ext

    def _dump(self):
        r"_dump() -> None :: Dump all persistent data to pickle files."
        if isinstance(self._persistent_vars, basestring):
            self._persistent_vars = (self._persistent_vars,)
        for varname in self._persistent_vars:
            self._dump_var(varname)

    def _load(self):
        r"_load() -> None :: Load all persistent data from pickle files."
        if isinstance(self._persistent_vars, basestring):
            self._persistent_vars = (self._persistent_vars,)
        for varname in self._persistent_vars:
            self._load_var(varname)

    def _dump_var(self, varname):
        r"_dump_var() -> None :: Dump a especific variable to a pickle file."
        f = file(self._pickle_filename(varname), 'wb')
        pickle.dump(getattr(self, varname), f, 2)
        f.close()

    def _load_var(self, varname):
        r"_load_var() -> object :: Load a especific pickle file."
        f = file(self._pickle_filename(varname))
        setattr(self, varname, pickle.load(f))
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
        _persistent_vars = ('some_var', 'other_var')
        _restorable_defaults = dict(
                some_var = 'some_default',
                other_var = 'other_default')

    The defaults is a dictionary, very coupled with the _persistent_vars
    attribute inherited from Persistent. The defaults keys should be the
    values from _persistent_vars, and the values the default values.

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
            return True
        except IOError:
            for (k, v) in self._restorable_defaults.items():
                setattr(self, k, v)
            self._dump()
            if hasattr(self, '_write_config'):
                self._write_config()
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
        _config_writer_cfg_dir = '/etc/service'
        _config_writer_tpl_dir = 'templates'

    The generated configuration files directory defaults to '.' and the
    templates directory to 'templates'. _config_writer_files has no default and
    must be specified in either way. It can be string or a tuple if more than
    one configuration file must be generated.

    The template filename and the generated configuration filename are both the
    same (so if you want to generate some /etc/config, you should have some
    templates/config template). That's why _config_writer_cfg_dir and
    _config_writer_tpl_dir can't be the same.

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
        if not config_filename:
            config_filename = template_name
        if vars is None:
            if hasattr(self, '_get_config_vars'):
                vars = self._get_config_vars(template_name)
            else:
                vars = dict()
        elif callable(vars):
            vars = vars(template_name)
        f = file(path.join(self._config_writer_cfg_dir, config_filename), 'w')
        ctx = Context(f, **vars)
        self._config_writer_templates[template_name].render_context(ctx)
        f.close()

    def _write_config(self):
        r"_write_config() -> None :: Generate all the configuration files."
        for t in self._config_writer_files:
            self._write_single_config(t)

class TransactionalHandler(Handler):
    r"""TransactionalHandler([initd_name[, initd_dir]]) -> TransactionalHandler.

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
        if hasattr(self, '_reload'):
            self.reload()

    @handler(u'Discard all the uncommited changes.')
    def rollback(self):
        r"rollback() -> None :: Discard the changes not yet commited."
        if hasattr(self, '_load'):
            self._load()


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
        _persistent_vars = 'vars'
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
        _persistent_vars = 'vars'
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


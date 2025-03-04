# vim: set encoding=utf-8 et sw=4 sts=4 :

import subprocess
from mako.template import Template
from mako.runtime import Context
from formencode.validators import Int
from formencode.schema import Schema
from os import path
try:
    import cPickle as pickle
except ImportError:
    import pickle
import logging ; log = logging.getLogger('pymin.service.util')

from pymin.dispatcher import Handler, handler, HandlerError, \
                                CommandNotFoundError
from pymin.seqtools import Sequence

#DEBUG = False
DEBUG = True

__all__ = ('Error', 'ExecutionError', 'ItemError', 'ItemAlreadyExistsError',
           'ItemNotFoundError', 'ContainerError', 'ContainerNotFoundError',
           'call', 'get_network_devices', 'Persistent', 'Restorable',
           'ConfigWriter', 'ServiceHandler', 'RestartHandler',
           'ReloadHandler', 'InitdHandler', 'SubHandler', 'DictSubHandler',
           'ListSubHandler', 'ComposedSubHandler', 'ListComposedSubHandler',
           'DictComposedSubHandler', 'Device','Address')

class IndexValidator(Schema):
    "Trivial schema validator for SubHandler's indexes"
    index = Int
    def to_python(self, value, state=None):
        # we want to return the index directly, the only purpose of this
        # validation being a schema is for field error reporting
        return super(Schema, self).to_python(dict(index=value), state)['index']

class Error(HandlerError):
    r"""
    Error(message) -> Error instance :: Base ServiceHandler exception class.

    All exceptions raised by the ServiceHandler inherits from this one, so
    you can easily catch any ServiceHandler exception.

    message - A descriptive error message.
    """
    pass

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
        self.message = u'Item already exists: %s' % key

class ItemNotFoundError(ItemError):
    r"""
    ItemNotFoundError(key) -> ItemNotFoundError instance.

    This exception is raised when trying to operate on an item that doesn't
    exists.
    """

    def __init__(self, key):
        r"Initialize the object. See class documentation for more info."
        self.message = u'Item not found: "%s"' % key

class ContainerError(Error, KeyError):
    r"""
    ContainerError(key) -> ContainerError instance.

    This is the base exception for all container related errors.
    """

    def __init__(self, key):
        r"Initialize the object. See class documentation for more info."
        self.message = u'Container error: "%s"' % key

class ContainerNotFoundError(ContainerError):
    r"""
    ContainerNotFoundError(key) -> ContainerNotFoundError instance.

    This exception is raised when trying to operate on an container that
    doesn't exists.
    """

    def __init__(self, key):
        r"Initialize the object. See class documentation for more info."
        self.message = u'Container not found: "%s"' % key

class Address(Sequence):
    def __init__(self, ip, netmask, broadcast=None, peer=None):
        self.ip = ip
        self.netmask = netmask
        self.broadcast = broadcast
        self.peer = peer
    def update(self, netmask=None, broadcast=None):
        if netmask is not None: self.netmask = netmask
        if broadcast is not None: self.broadcast = broadcast
    def as_tuple(self):
        return (self.ip, self.netmask, self.broadcast, self.peer)


class Device(Sequence):
    def __init__(self, name, mac, ppp):
        self.name = name
        self.mac = mac
        self.ppp = ppp
        self.active = True
        self.addrs = dict()
        self.routes = list()
    def as_tuple(self):
        return (self.name, self.mac, self.active, self.addrs)



def get_network_devices():
    p = subprocess.Popen(('ip', '-o', 'link'), stdout=subprocess.PIPE,
                                                    close_fds=True)
    string = p.stdout.read()
    p.wait()
    d = dict()
    devices = string.splitlines()
    for dev in devices:
        mac = ''
        if dev.find('link/ether') != -1:
            i = dev.find('link/ether')
            mac = dev[i+11 : i+11+17]
            i = dev.find(':')
            j = dev.find(':', i+1)
            name = dev[i+2: j]
            d[name] = Device(name,mac,False)
        elif dev.find('link/ppp') != -1:
            i = dev.find('link/ppp')
            mac =  '00:00:00:00:00:00'
            i = dev.find(':')
            j = dev.find(':', i+1)
            name = dev[i+2 : j]
            d[name] = Device(name,mac,True)
            #since the device is ppp, get the address and peer
            try:
                p = subprocess.Popen(('ip', '-o', 'addr', 'show', name), stdout=subprocess.PIPE,
                                                        close_fds=True, stderr=subprocess.PIPE)
                string = p.stdout.read()
                p.wait()
                addrs = string.splitlines()
                inet = addrs[1].find('inet')
                peer = addrs[1].find('peer')
                bar = addrs[1].find('/')
                from_addr = addrs[1][inet+5 : peer-1]
                to_addr = addrs[1][peer+5 : bar]
                d[name].addrs[from_addr] = Address(from_addr,24, peer=to_addr)
            except IndexError:
                pass
    return d

def get_peers():
    p = subprocess.Popen(('ip', '-o', 'addr'), stdout=subprocess.PIPE,
                                                    close_fds=True)

def call(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, close_fds=True, universal_newlines=True,
            **kw):
    log.debug(u'call(%r)', command)
    if DEBUG:
        log.debug(u'call: not really executing, DEBUG mode')
        return
    try:
        subprocess.check_call(command, stdin=stdin, stdout=stdout,
                    stderr=stderr, close_fds=close_fds,
                    universal_newlines=universal_newlines, **kw)
    except Exception, e:
        log.debug(u'call: Execution error %r', e)
        raise ExecutionError(command, e)

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
        fname = self._pickle_filename(attrname)
        attr = getattr(self, attrname)
        log.debug(u'Persistent._dump_attr(%r) -> file=%r, value=%r',
                attrname, fname, attr)
        f = file(self._pickle_filename(attrname), 'wb')
        pickle.dump(attr, f, 2)
        f.close()

    def _load_attr(self, attrname):
        r"_load_attr() -> object :: Load a specific pickle file."
        fname = self._pickle_filename(attrname)
        f = file(fname)
        attr = pickle.load(f)
        log.debug(u'Persistent._load_attr(%r) -> file=%r, value=%r',
                attrname, fname, attr)
        setattr(self, attrname, attr)
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
        log.debug(u'Restorable._restore()')
        try:
            log.debug(u'Restorable._restore: trying to load...')
            self._load()
            log.debug(u'Restorable._restore: load OK')
            return True
        except IOError:
            log.debug(u'Restorable._restore: load FAILED, making defaults: %r',
                        self._restorable_defaults)
            for (k, v) in self._restorable_defaults.items():
                setattr(self, k, v)
            # TODO tener en cuenta servicios que hay que levantar y los que no
            if hasattr(self, 'commit'):
                log.debug(u'Restorable._restore: commit() found, commiting...')
                self.commit()
                return False
            log.debug(u'Restorable._restore: dumping new defaults...')
            self._dump()
            if hasattr(self, '_write_config'):
                log.debug(u'Restorable._restore: _write_config() found, '
                            u'writing new config...')
                self._write_config()
            return False

class ConfigWriter:
    r"""ConfigWriter([files[, cfg_dir[, tpl_dir]]]) -> ConfigWriter.

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
        log.debug(u'ConfigWriter.build_templates()')
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
        log.debug(u'ConfigWriter._render_config: rendering template %r with '
                    u'vars=%r', template_name, vars)
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
        fname = self._get_config_path(template_name, config_filename)
        f = file(fname, 'w')
        ctx = Context(f, **vars)
        log.debug(u'ConfigWriter._write_single_config: rendering template '
                    u'%r with vars=%r to file %r', template_name, vars, fname)
        self._config_writer_templates[template_name].render_context(ctx)
        f.close()

    def _write_config(self):
        r"_write_config() -> None :: Generate all the configuration files."
        for t in self._config_writer_files:
            self._write_single_config(t)


class ServiceHandler(Handler, Restorable):
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
        log.debug(u'ServiceHandler(%r, %r, %r, %r)', start, stop, restart,
                    reload)
        for (name, action) in dict(start=start, stop=stop, restart=restart,
                                                    reload=reload).items():
            if action is not None:
                attr_name = '_service_%s' % name
                log.debug(u'ServiceHandler: using %r as %s', attr_name, action)
                setattr(self, attr_name, action)
        self._persistent_attrs = list(self._persistent_attrs)
        self._persistent_attrs.append('_service_running')
        if '_service_running' not in self._restorable_defaults:
            self._restorable_defaults['_service_running'] = False
        log.debug(u'ServiceHandler: restoring service configuration...')
        self._restore()
        if self._service_running:
            log.debug(u'ServiceHandler: service was running, starting it...')
            self._service_running = False
            self.start()

    @handler(u'Start the service.')
    def start(self):
        r"start() -> None :: Start the service."
        log.debug(u'ServiceHandler.start()')
        if not self._service_running:
            log.debug(u'ServiceHandler.start: not running, starting it...')
            if callable(self._service_start):
                self._service_start()
            else:
                call(self._service_start)
            self._service_running = True
            self._dump_attr('_service_running')

    @handler(u'Stop the service.')
    def stop(self):
        log.debug(u'ServiceHandler.stop()')
        r"stop() -> None :: Stop the service."
        if self._service_running:
            log.debug(u'ServiceHandler.stop: running, stoping it...')
            if callable(self._service_stop):
                self._service_stop()
            else:
                call(self._service_stop)
            self._service_running = False
            self._dump_attr('_service_running')

    @handler(u'Restart the service.')
    def restart(self):
        r"restart() -> None :: Restart the service."
        log.debug(u'ServiceHandler.restart()')
        if callable(self._service_restart):
            self._service_restart()
        else:
            call(self._service_restart)
        self._service_running = True
        self._dump_attr('_service_running')

    @handler(u'Reload the service config (without restarting, if possible).')
    def reload(self):
        r"reload() -> None :: Reload the configuration of the service."
        log.debug(u'ServiceHandler.reload()')
        if self._service_running:
            log.debug(u'ServiceHandler.reload: running, reloading...')
            if callable(self._service_reload):
                self._service_reload()
            else:
                call(self._service_reload)

    @handler(u'Tell if the service is running.')
    def running(self):
        r"reload() -> None :: Reload the configuration of the service."
        log.debug(u'ServiceHandler.running() -> %r', self._service_running)
        if self._service_running:
            return 1
        else:
            return 0

class RestartHandler(Handler):
    r"""RestartHandler() -> RestartHandler :: Provides generic restart command.

    This is a helper class to inherit from to automatically add a restart
    command that first stop the service and then starts it again (using start
    and stop commands respectively).
    """

    @handler(u'Restart the service (alias to stop + start).')
    def restart(self):
        r"restart() -> None :: Restart the service calling stop() and start()."
        log.debug(u'RestartHandler.restart()')
        self.stop()
        self.start()

class ReloadHandler(Handler):
    r"""ReloadHandler() -> ReloadHandler :: Provides generic reload command.

    This is a helper class to inherit from to automatically add a reload
    command that calls restart.
    """

    @handler(u'Reload the service config (alias to restart).')
    def reload(self):
        r"reload() -> None :: Reload the configuration of the service."
        log.debug(u'ReloadHandler.reload()')
        if hasattr(self, '_service_running') and self._service_running:
            log.debug(u'ReloadHandler.reload: running, reloading...')
            self.restart()

class InitdHandler(ServiceHandler):
    # TODO update docs, declarative style is depracated
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
        log.debug(u'InitdHandler(%r, %r)', initd_name, initd_dir)
        if initd_name is not None:
            self._initd_name = initd_name
        if initd_dir is not None:
            self._initd_dir = initd_dir
        actions = dict()
        for action in ('start', 'stop', 'restart', 'reload'):
            actions[action] = (path.join(self._initd_dir, self._initd_name),
                                action)
        ServiceHandler.__init__(self, **actions)

    def handle_timer(self):
        # TODO documentation
        log.debug(u'InitdHandler.handle_timer(): self=%r', self)
        p = subprocess.Popen(('pgrep', '-f', self._initd_name),
                                stdout=subprocess.PIPE)
        pid = p.communicate()[0]
        if p.returncode == 0 and len(pid) > 0:
            log.debug(u'InitdHandler.handle_timer: pid present, running')
            self._service_running = True
        else:
            log.debug(u'InitdHandler.handle_timer: pid absent, NOT running')
            self._service_running = False

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
        log.debug(u'TransactionalHandler.commit()')
        if hasattr(self, '_dump'):
            log.debug(u'TransactionalHandler.commit: _dump() present, '
                        u'dumping...')
            self._dump()
        unchanged = False
        if hasattr(self, '_write_config'):
            log.debug(u'TransactionalHandler.commit: _write_config() present, '
                        u'writing config...')
            unchanged = self._write_config()
        if not unchanged and hasattr(self, 'reload'):
            log.debug(u'TransactionalHandler.commit: reload() present, and'
                        u'configuration changed, reloading...')
            self.reload()

    @handler(u'Discard all the uncommited changes.')
    def rollback(self):
        r"rollback() -> None :: Discard the changes not yet commited."
        log.debug(u'TransactionalHandler.reload()')
        if hasattr(self, '_load'):
            log.debug(u'TransactionalHandler.reload: _load() present, loading'
                        u'pickled values...')
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
        log.debug(u'ParametersHandler(%r)', attr)
        if attr is not None:
            self._parameters_attr = attr

    @handler(u'Set a service parameter.')
    def set(self, param, value):
        r"set(param, value) -> None :: Set a service parameter."
        log.debug(u'ParametersHandler.set(%r, %r)', param, value)
        if not param in self.params:
            log.debug(u'ParametersHandler.set: parameter not found')
            raise ParameterNotFoundError(param)
        self.params[param] = value
        if hasattr(self, '_update'):
            log.debug(u'ParametersHandler.set: _update found, setting to True')
            self._update = True

    @handler(u'Get a service parameter.')
    def get(self, param):
        r"get(param) -> None :: Get a service parameter."
        log.debug(u'ParametersHandler.get(%r)', param)
        if not param in self.params:
            log.debug(u'ParametersHandler.get: parameter not found')
            raise ParameterNotFoundError(param)
        return self.params[param]

    @handler(u'List all available service parameters.')
    def list(self):
        r"list() -> tuple :: List all the parameter names."
        log.debug(u'ParametersHandler.list()')
        return self.params.keys()

    @handler(u'Get all service parameters, with their values.')
    def show(self):
        r"show() -> (key, value) tuples :: List all the parameters."
        log.debug(u'ParametersHandler.show()')
        return self.params.items()

class SubHandler(Handler):
    r"""SubHandler(parent) -> SubHandler instance :: Handles subcommands.

    This is a helper class to build sub handlers that needs to reference the
    parent handler.

    parent - Parent Handler object.
    """

    def __init__(self, parent):
        r"Initialize the object, see the class documentation for details."
        log.debug(u'SubHandler(%r)', parent)
        self.parent = parent

class ContainerSubHandler(SubHandler):
    r"""ContainerSubHandler(parent) -> ContainerSubHandler instance.

    This is a helper class to implement ListSubHandler and DictSubHandler. You
    should not use it directly.

    The container attribute to handle and the class of objects that it
    contains can be defined by calling the constructor or in a more declarative
    way as class attributes, like:

    class TestHandler(ContainerSubHandler):
        _cont_subhandler_attr = 'some_cont'
        _cont_subhandler_class = SomeClass

    This way, the parent's some_cont attribute (self.parent.some_cont)
    will be managed automatically, providing the commands: add, update,
    delete, get and show. New items will be instances of SomeClass,
    which should provide a cmp operator to see if the item is on the
    container and an update() method, if it should be possible to modify
    it. If SomeClass has an _add, _update or _delete attribute, it set
    them to true when the item is added, updated or deleted respectively
    (in case that it's deleted, it's not removed from the container,
    but it's not listed either).
    """

    def __init__(self, parent, attr=None, cls=None):
        r"Initialize the object, see the class documentation for details."
        log.debug(u'ContainerSubHandler(%r, %r, %r)', parent, attr, cls)
        self.parent = parent
        if attr is not None:
            self._cont_subhandler_attr = attr
        if cls is not None:
            self._cont_subhandler_class = cls

    def _attr(self, attr=None):
        if attr is None:
            return getattr(self.parent, self._cont_subhandler_attr)
        setattr(self.parent, self._cont_subhandler_attr, attr)

    def _vattr(self):
        if isinstance(self._attr(), dict):
            return dict([(k, i) for (k, i) in self._attr().items()
                    if not hasattr(i, '_delete') or not i._delete])
        return [i for i in self._attr()
                if not hasattr(i, '_delete') or not i._delete]

    @handler(u'Add a new item')
    def add(self, *args, **kwargs):
        r"add(...) -> None :: Add an item to the list."
        log.debug(u'ContainerSubHandler.add(%r, %r)', args, kwargs)
        item = self._cont_subhandler_class(*args, **kwargs)
        if hasattr(item, '_add'):
            log.debug(u'ContainerSubHandler.add: _add found, setting to True')
            item._add = True
        key = item
        if isinstance(self._attr(), dict):
            key = item.as_tuple()[0]
        # do we have the same item? then raise an error
        if key in self._vattr():
            log.debug(u'ContainerSubHandler.add: allready exists')
            if not isinstance(self._attr(), dict):
                key = self._attr().index(item)
            raise ItemAlreadyExistsError(key)
        # do we have the same item, but logically deleted? then update flags
        if key in self._attr():
            log.debug(u'ContainerSubHandler.add: was deleted, undeleting it')
            index = key
            if not isinstance(self._attr(), dict):
                index = self._attr().index(item)
            if hasattr(item, '_add'):
                self._attr()[index]._add = False
            if hasattr(item, '_delete'):
                self._attr()[index]._delete = False
        else: # it's *really* new
            if isinstance(self._attr(), dict):
                self._attr()[key] = item
            else:
                self._attr().append(item)

    @handler(u'Update an item')
    def update(self, index, *args, **kwargs):
        r"update(index, ...) -> None :: Update an item of the container."
        log.debug(u'ContainerSubHandler.update(%r, %r, %r)',
                    index, args, kwargs)
        # TODO make it right with metaclasses, so the method is not created
        # unless the update() method really exists.
        if not isinstance(self._attr(), dict):
            index = IndexValidator.to_python(index)
        if not hasattr(self._cont_subhandler_class, 'update'):
            log.debug(u'ContainerSubHandler.update: update() not found, '
                        u"can't really update, raising command not found")
            raise CommandNotFoundError(('update',))
        try:
            item = self._vattr()[index]
            item.update(*args, **kwargs)
            if hasattr(item, '_update'):
                log.debug(u'ContainerSubHandler.update: _update found, '
                            u'setting to True')
                item._update = True
        except LookupError:
            log.debug(u'ContainerSubHandler.update: item not found')
            raise ItemNotFoundError(index)

    @handler(u'Delete an item')
    def delete(self, index):
        r"delete(index) -> None :: Delete an item of the container."
        log.debug(u'ContainerSubHandler.delete(%r)', index)
        if not isinstance(self._attr(), dict):
            index = IndexValidator.to_python(index)
        try:
            item = self._vattr()[index]
            if hasattr(item, '_delete'):
                log.debug(u'ContainerSubHandler.delete: _delete found, '
                            u'setting to True')
                item._delete = True
            else:
                del self._attr()[index]
            return item
        except LookupError:
            log.debug(u'ContainerSubHandler.delete: item not found')
            raise ItemNotFoundError(index)

    @handler(u'Remove all items (use with care).')
    def clear(self):
        r"clear() -> None :: Delete all items of the container."
        log.debug(u'ContainerSubHandler.clear()')
        # FIXME broken really, no _delete attribute is setted :S
        if isinstance(self._attr(), dict):
            self._attr().clear()
        else:
            self._attr(list())

    @handler(u'Get information about an item')
    def get(self, index):
        r"get(index) -> item :: List all the information of an item."
        log.debug(u'ContainerSubHandler.get(%r)', index)
        if not isinstance(self._attr(), dict):
            index = IndexValidator.to_python(index)
        try:
            return self._vattr()[index]
        except LookupError:
            log.debug(u'ContainerSubHandler.get: item not found')
            raise ItemNotFoundError(index)

    @handler(u'Get information about all items')
    def show(self):
        r"show() -> list of items :: List all the complete items information."
        log.debug(u'ContainerSubHandler.show()')
        if isinstance(self._attr(), dict):
            return self._attr().values()
        return self._vattr()

class ListSubHandler(ContainerSubHandler):
    r"""ListSubHandler(parent) -> ListSubHandler instance.

    ContainerSubHandler holding lists. See ComposedSubHandler documentation
    for details.
    """

    @handler(u'Get how many items are in the list')
    def len(self):
        r"len() -> int :: Get how many items are in the list."
        log.debug(u'ListContainerSubHandler.len()')
        return len(self._vattr())

class DictSubHandler(ContainerSubHandler):
    r"""DictSubHandler(parent) -> DictSubHandler instance.

    ContainerSubHandler holding dicts. See ComposedSubHandler documentation
    for details.
    """

    @handler(u'List all the items by key')
    def list(self):
        r"list() -> tuple :: List all the item keys."
        log.debug(u'DictContainerSubHandler.list()')
        return self._attr().keys()

class ComposedSubHandler(SubHandler):
    r"""ComposedSubHandler(parent) -> ComposedSubHandler instance.

    This is a helper class to implement ListComposedSubHandler and
    DictComposedSubHandler. You should not use it directly.

    This class is usefull when you have a parent that has a dict (cont)
    that stores some object that has an attribute (attr) with a list or
    a dict of objects of some class. In that case, this class provides
    automated commands to add, update, delete, get and show that objects.
    This commands takes the cont (key of the dict for the object holding
    the attr), and an index for access the object itself (in the attr
    list/dict).

    The container object (cont) that holds a containers, the attribute of
    that object that is the container itself, and the class of the objects
    that it contains can be defined by calling the constructor or in a
    more declarative way as class attributes, like:

    class TestHandler(ComposedSubHandler):
        _comp_subhandler_cont = 'some_cont'
        _comp_subhandler_attr = 'some_attr'
        _comp_subhandler_class = SomeClass

    This way, the parent's some_cont attribute (self.parent.some_cont)
    will be managed automatically, providing the commands: add, update,
    delete, get and show for manipulating a particular instance that holds
    of SomeClass. For example, updating an item at the index 5 is the same
    (simplified) as doing parent.some_cont[cont][5].update().
    SomeClass should provide a cmp operator to see if the item is on the
    container and an update() method, if it should be possible to modify
    it. If SomeClass has an _add, _update or _delete attribute, it set
    them to true when the item is added, updated or deleted respectively
    (in case that it's deleted, it's not removed from the container,
    but it's not listed either). If the container objects
    (parent.some_cont[cont]) has an _update attribute, it's set to True
    when any add, update or delete command is executed.
    """

    def __init__(self, parent, cont=None, attr=None, cls=None):
        r"Initialize the object, see the class documentation for details."
        log.debug(u'ComposedSubHandler(%r, %r, %r, %r)',
                    parent, cont, attr, cls)
        self.parent = parent
        if cont is not None:
            self._comp_subhandler_cont = cont
        if attr is not None:
            self._comp_subhandler_attr = attr
        if cls is not None:
            self._comp_subhandler_class = cls

    def _cont(self):
        return getattr(self.parent, self._comp_subhandler_cont)

    def _attr(self, cont, attr=None):
        if attr is None:
            return getattr(self._cont()[cont], self._comp_subhandler_attr)
        setattr(self._cont()[cont], self._comp_subhandler_attr, attr)

    def _vattr(self, cont):
        if isinstance(self._attr(cont), dict):
            return dict([(k, i) for (k, i) in self._attr(cont).items()
                    if not hasattr(i, '_delete') or not i._delete])
        return [i for i in self._attr(cont)
                if not hasattr(i, '_delete') or not i._delete]

    @handler(u'Add a new item')
    def add(self, cont, *args, **kwargs):
        r"add(cont, ...) -> None :: Add an item to the list."
        log.debug(u'ComposedSubHandler.add(%r, %r, %r)', cont, args, kwargs)
        if not cont in self._cont():
            log.debug(u'ComposedSubHandler.add: container not found')
            raise ContainerNotFoundError(cont)
        item = self._comp_subhandler_class(*args, **kwargs)
        if hasattr(item, '_add'):
            log.debug(u'ComposedSubHandler.add: _add found, setting to True')
            item._add = True
        key = item
        if isinstance(self._attr(cont), dict):
            key = item.as_tuple()[0]
        # do we have the same item? then raise an error
        if key in self._vattr(cont):
            log.debug(u'ComposedSubHandler.add: allready exists')
            if not isinstance(self._attr(cont), dict):
                key = self._attr(cont).index(item)
            raise ItemAlreadyExistsError(key)
        # do we have the same item, but logically deleted? then update flags
        if key in self._attr(cont):
            log.debug(u'ComposedSubHandler.add: was deleted, undeleting it')
            index = key
            if not isinstance(self._attr(cont), dict):
                index = self._attr(cont).index(item)
            if hasattr(item, '_add'):
                self._attr(cont)[index]._add = False
            if hasattr(item, '_delete'):
                self._attr(cont)[index]._delete = False
        else: # it's *really* new
            if isinstance(self._attr(cont), dict):
                self._attr(cont)[key] = item
            else:
                self._attr(cont).append(item)
        if hasattr(self._cont()[cont], '_update'):
            log.debug(u"ComposedSubHandler.add: container's _update found, "
                        u'setting to True')
            self._cont()[cont]._update = True

    @handler(u'Update an item')
    def update(self, cont, index, *args, **kwargs):
        r"update(cont, index, ...) -> None :: Update an item of the container."
        # TODO make it right with metaclasses, so the method is not created
        # unless the update() method really exists.
        log.debug(u'ComposedSubHandler.update(%r, %r, %r, %r)',
                    cont, index, args, kwargs)
        if not cont in self._cont():
            log.debug(u'ComposedSubHandler.add: container not found')
            raise ContainerNotFoundError(cont)
        if not isinstance(self._attr(cont), dict):
            index = IndexValidator.to_python(index)
        if not hasattr(self._comp_subhandler_class, 'update'):
            log.debug(u'ComposedSubHandler.update: update() not found, '
                        u"can't really update, raising command not found")
            raise CommandNotFoundError(('update',))
        try:
            item = self._vattr(cont)[index]
            item.update(*args, **kwargs)
            if hasattr(item, '_update'):
                log.debug(u'ComposedSubHandler.update: _update found, '
                            u'setting to True')
                item._update = True
            if hasattr(self._cont()[cont], '_update'):
                log.debug(u"ComposedSubHandler.add: container's _update found, "
                            u'setting to True')
                self._cont()[cont]._update = True
        except LookupError:
            log.debug(u'ComposedSubHandler.update: item not found')
            raise ItemNotFoundError(index)

    @handler(u'Delete an item')
    def delete(self, cont, index):
        r"delete(cont, index) -> None :: Delete an item of the container."
        log.debug(u'ComposedSubHandler.delete(%r, %r)', cont, index)
        if not cont in self._cont():
            log.debug(u'ComposedSubHandler.add: container not found')
            raise ContainerNotFoundError(cont)
        if not isinstance(self._attr(cont), dict):
            index = IndexValidator.to_python(index)
        try:
            item = self._vattr(cont)[index]
            if hasattr(item, '_delete'):
                log.debug(u'ComposedSubHandler.delete: _delete found, '
                            u'setting to True')
                item._delete = True
            else:
                del self._attr(cont)[index]
            if hasattr(self._cont()[cont], '_update'):
                log.debug(u"ComposedSubHandler.add: container's _update found, "
                            u'setting to True')
                self._cont()[cont]._update = True
            return item
        except LookupError:
            log.debug(u'ComposedSubHandler.delete: item not found')
            raise ItemNotFoundError(index)

    @handler(u'Remove all items (use with care).')
    def clear(self, cont):
        r"clear(cont) -> None :: Delete all items of the container."
        # FIXME broken really, no item or container _delete attribute is
        #       setted :S
        log.debug(u'ComposedSubHandler.clear(%r)', cont)
        if not cont in self._cont():
            log.debug(u'ComposedSubHandler.add: container not found')
            raise ContainerNotFoundError(cont)
        if isinstance(self._attr(cont), dict):
            self._attr(cont).clear()
        else:
            self._attr(cont, list())

    @handler(u'Get information about an item')
    def get(self, cont, index):
        r"get(cont, index) -> item :: List all the information of an item."
        log.debug(u'ComposedSubHandler.get(%r, %r)', cont, index)
        if not cont in self._cont():
            log.debug(u'ComposedSubHandler.add: container not found')
            raise ContainerNotFoundError(cont)
        if not isinstance(self._attr(cont), dict):
            index = IndexValidator.to_python(index)
        try:
            return self._vattr(cont)[index]
        except LookupError:
            log.debug(u'ComposedSubHandler.get: item not found')
            raise ItemNotFoundError(index)

    @handler(u'Get information about all items')
    def show(self, cont):
        r"show(cont) -> list of items :: List all the complete items information."
        log.debug(u'ComposedSubHandler.show(%r)', cont)
        if not cont in self._cont():
            log.debug(u'ComposedSubHandler.add: container not found')
            raise ContainerNotFoundError(cont)
        if isinstance(self._attr(cont), dict):
            return self._attr(cont).values()
        return self._vattr(cont)

class ListComposedSubHandler(ComposedSubHandler):
    r"""ListComposedSubHandler(parent) -> ListComposedSubHandler instance.

    ComposedSubHandler holding lists. See ComposedSubHandler documentation
    for details.
    """

    @handler(u'Get how many items are in the list')
    def len(self, cont):
        r"len(cont) -> int :: Get how many items are in the list."
        log.debug(u'ListComposedSubHandler.len(%r)', cont)
        if not cont in self._cont():
            raise ContainerNotFoundError(cont)
        return len(self._vattr(cont))

class DictComposedSubHandler(ComposedSubHandler):
    r"""DictComposedSubHandler(parent) -> DictComposedSubHandler instance.

    ComposedSubHandler holding dicts. See ComposedSubHandler documentation
    for details.
    """

    @handler(u'List all the items by key')
    def list(self, cont):
        r"list(cont) -> tuple :: List all the item keys."
        log.debug(u'DictComposedSubHandler.list(%r)', cont)
        if not cont in self._cont():
            raise ContainerNotFoundError(cont)
        return self._attr(cont).keys()


if __name__ == '__main__':

    logging.basicConfig(
        level   = logging.DEBUG,
        format  = '%(asctime)s %(levelname)-8s %(message)s',
        datefmt = '%H:%M:%S',
    )

    import sys

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

    print get_network_devices()


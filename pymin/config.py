# vim: set encoding=utf-8 et sw=4 sts=4 :

# TODO
#
# * add 'append' mode to ListOption (like ConfigOption).
#
# * update/write documentation

import os
import re
import sys
import shlex
import optparse
from formencode import Schema, ForEach, Invalid, validators
from ConfigParser import SafeConfigParser, InterpolationMissingOptionError, \
                         InterpolationSyntaxError, InterpolationDepthError, \
                         MissingSectionHeaderError, ParsingError
import logging ; log = logging.getLogger('pymin.config')


__all__ = ('ConfigError', 'MissingSectionHeaderError', 'ParsingError',
           'Options', 'OptionGroup', 'Option',
           'VOID', 'load_config', 'config', 'options')


# regular expression to check if a name is a valid python identifier
identifier_re = re.compile(r'^[a-zA-Z_]\w*$')


class ConfigError(RuntimeError):
    """
    Raised when the problem is due to an user error.
    """
    pass


class VoidClass:
    def __repr__(self):
        return "<void>"
    def __len__(self):
        "For boolean expression evaluation"
        return 0
VOID = VoidClass()


class Options:
    """
    Represent a set of options a program can have.

    Both command-line and configuration file options are handled.

    .. attr:: default_group

        The name of the default :class:`OptionGroup`. Options that
        don't belong to any group are looked in the section with this
        name in the config file.

    .. attr:: default_group

        Default :class:`OptionGroup` description.

    .. attr:: options

        A list of :class:`Option` or :class:`OptionGroup`
        instances. Groups are translated to a section when parsing the
        config file, and to prefixes in the long options when parsing
        the command-line.
    """

    def __init__(self, schemacls=None):
        self.default_group = ''
        self.default_group_desc = ''
        self.options = []
        if schemacls is None:
            schemacls = Schema
        self.schemacls = schemacls
        self.schema = None # filled in process()

    def add(self, options):
        log.debug('Options.add(%r)', options)
        if isinstance(options, (list, tuple)):
            self.options.extend(options)
        else:
            self.options.append(options)

    def add_group(self, *args, **kwargs):
        g = OptionGroup(*args, **kwargs)
        log.debug('Options.add_group(%r)', g)
        self.add(g)

    def get_group(self, group_name):
        for g in self.options:
            if isinstance(g, OptionGroup) and g.name == group_name:
                return g

    def init(self, default_group=None, default_group_desc=None,
             options=None):
        """
        Initialize the class. Since the class is instantiated by the
        config framework, you should use this method to set it's values.

        Arguments are directly mapped to the class attributes, with
        the particularity of options being appended to existing options
        (instead of replaced).
        """
        log.debug('Options.init(default_group=%r, default_group_desc=%r, '
                  'options=%r)', default_group, default_group_desc, options)
        if not identifier_re.match(default_group):
            raise ValueError("Invalid default group name '%s' (group names "
                             "must be valid python identifiers" % name)
        if default_group is not None:
            self.default_group = default_group
        if default_group_desc is not None:
            self.default_group_desc = default_group_desc
        if options is not None:
            self.options.extend(options)

    def process(self, parser):
        """
        Process the command-line options.

        ``parser`` should be a :class:`optparse.OptionParser` instance.
        """
        log.debug('Options.process()')
        self.schema = self.schemacls()
        config_opts = []
        for o in self.options:
            o.process(parser, self.schema, config_opts, self.default_group)
        return config_opts

    def values(self, confparser, parseropts, ignore_errors):
        """
        Post process the command-line options.

        ``config`` should be an object where options are stored. If
        ``prefix`` is specified, the prefix will be used to look for
        the option.
        """
        log.debug('Options.values()')
        # first populate the confparser with the values from the command-line
        # options to make the variable interpolation works as expected.
        for o in self.options:
            o.set_value(confparser, parseropts, self.default_group)
        # then, get the actual values
        v = dict()
        for o in self.options:
            v[o.name] = o.value(confparser, parseropts, self.default_group,
                                ignore_errors)
        log.debug('Options.values() -> %r', v)
        return v

    @property
    def defaults(self):
        log.debug('Options.defaults()')
        defaults = dict()
        for o in self.options:
            defaults.update(o.defaults)
        log.debug('Options.defaults() -> %r', defaults)
        return defaults


class OptionGroup:

    def __init__(self, name, description=None, options=None):
        log.debug('OptionGroup(name=%r, description=%r, options=%r)', name,
                  description, options)
        if not identifier_re.match(name):
            raise ValueError("Invalid group name '%s' (group names must be "
                             "valid python identifiers" % name)
        self.name = name
        self.oname = name.replace('_', '-')
        self.description = description
        self.options = []
        if options is not None:
            self.add(options)

    def add(self, options):
        log.debug('OptionGroup.add(%r)', options)
        if not isinstance(options, (list, tuple)):
            options = [options]
        for o in options:
            if isinstance(o, OptionGroup):
                raise ConfigError("Groups can't be nested (group '%s' found "
                                  "inside group '%s')" % (o.name, self.name))
        self.options.extend(options)

    def process(self, parser, schema, config_opts, default_group):
        """
        Process the command-line options.

        ``parser`` should be a :class:`optparse.OptionParser` instance.
        """
        subschema = schema.__class__()
        group = optparse.OptionGroup(parser, self.description)
        for o in self.options:
            if o.short:
                raise ValueError("Grouped options can't have short name "
                                  "(option '%s' in grupo '%s' have this short "
                                  "names: %s)" % (o.name, self.name,
                                            ','.join('-' + o for o in o.short)))
            o.process(group, subschema, config_opts, self)
        log.debug('Adding group %s to optparse')
        parser.add_option_group(group)
        schema.add_field(self.name, subschema)

    def value(self, confparser, parseropts, default_group, ignore_errors):
        """
        """
        v = dict()
        for o in self.options:
            v[o.name] = o.value(confparser, parseropts, self, ignore_errors)
        return v

    def set_value(self, confparser, parseropts, default_group):
        """
        """
        v = dict()
        for o in self.options:
            o.set_value(confparser, parseropts, self)
        return v

    @property
    def defaults(self):
        defaults = dict()
        for o in self.options:
            defaults.update(o.defaults)
        defaults = { self.oname: defaults }
        return defaults

    def __repr__(self):
        return 'OptionGroup<%s>%r' % (self.name, self.options)


class Option:
    """
    A program's option.

    .. attr:: name

        The name of the option. The config object will have an attribute
        with this name. When parsing configuration and command-line
        options, the ``_`` in this name are replace with ``-``.

    .. attr:: validator

        See :mod:`formencode.validators` for available validators.

    .. attr:: short

        Short aliases (only for command-line options).

    .. attr:: long

        Long aliases.

    .. attr:: default

        Default value.

    .. attr:: help

        Help message for the option.

    .. attr:: metavar

        Name of the option argument used in the help message.

    """

    def __init__(self, name, validator=None, short=(), long=(), default=VOID,
                 help=VOID, metavar=VOID):
        log.debug('Option(name=%r, validator=%r, short=%r, long=%r, '
                  'default=%r, help=%r, metavar=%r)', name, validator, short,
                  long, default, help, metavar)
        if not identifier_re.match(name):
            raise ValueError("Invalid option name '%s' (option names must be "
                             "valid python identifiers" % name)
        self.name = name
        self.oname = name.replace('_', '-')
        self.validator = validator
        if isinstance(short, basestring):
            short = [short]
        self.short = list(short)
        if isinstance(long, basestring):
            long = [long]
        self.long = [self.oname] + list(long)
        self.default = default
        self.help = help
        self.metavar = metavar

    def process(self, parser, schema, config_opts, group):
        """
        Process the command-line options.

        ``parser`` should be a :class:`optparse.OptionParser` instance. If
        ``prefix`` is specified, all long command-line options are
        prefixed with that. For example: ``some_option`` will become
        ``--prefix-some-option``.
        """
        if isinstance(group, basestring):
            group = None
        parser.add_option(type='string', dest=self.dest(group), default=VOID,
                          metavar=self.metavar, help=self.help,
                          *self.optparser_args(group))
        log.debug('Option<%s>.process() -> add_option(%s, type=%r, dest=%r, '
                  'default=%r, metavar=%r, help=%r)', self.name,
                  ', '.join(repr(i) for i in self.optparser_args(group)),
                  'string', self.dest(group), VOID, self.metavar, self.help)
        schema.add_field(self.name, self.validator)

    def value(self, confparser, parseropts, group, ignore_errors):
        """
        Post process the command-line options.

        ``config`` should be an object where options are stored. If
        ``prefix`` is specified, the prefix will be used to look for
        the option.
        """
        section = group
        if isinstance(group, OptionGroup):
            section = group.oname
        if (confparser.has_section(section)
                    and confparser.has_option(section, self.oname)):
            return confparser.get(section, self.oname)
        if self.default is VOID:
            if ignore_errors:
                return None
            raise ConfigError('mandatory option "%s" not present' % self.name)
        return self.default

    def set_value(self, confparser, parseropts, group):
        val = getattr(parseropts, self.dest(group))
        if val is not VOID:
            section = group
            if isinstance(group, OptionGroup):
                section = group.oname
            if not confparser.has_section(section):
                confparser.add_section(section)
            confparser.set(section, self.oname, val)

    def optparser_args(self, group=None):
        args = []
        args.extend('-' + s for s in self.short)
        prefix = ''
        if group:
            prefix = group.oname + '-'
        args.extend('--' + prefix + l for l in self.long)
        return args

    def dest(self, group=None):
        prefix = ''
        if group and not isinstance(group, basestring):
            prefix = group.name + '.'
        return prefix + self.name

    @property
    def defaults(self):
        default = {}
        if self.default is not VOID:
            default[self.oname] = str(self.default)
        return default

    def __repr__(self):
        return 'Option<%s>' % (self.name)


class ListOption(Option):

    def process(self, parser, schema, config_opts, group):
        """
        """
        if isinstance(group, basestring):
            group = None
        parser.add_option(type='string', dest=self.dest(group), default=[],
                          metavar=self.metavar, help=self.help,
                          action='append', *self.optparser_args(group))
        log.debug('Option<%s>.process() -> add_option(%s, type=%r, dest=%r, '
                  'action=%r, default=%r, metavar=%r, help=%r)', self.name,
                  ', '.join(repr(i) for i in self.optparser_args(group)),
                  'string', self.dest(group), 'append', [], self.metavar,
                  self.help)
        schema.add_field(self.name, ForEach(self.validator, if_empty=[]))

    def value(self, confparser, parseropts, group, ignore_errors):
        """
        """
        value = Option.value(self, confparser, parseropts, group, ignore_errors)
        if not isinstance(value, (list, tuple)):
            value = shlex.split(value)
        return value

    def set_value(self, confparser, parseropts, group):
        val = getattr(parseropts, self.dest(group))
        if val:
            val = ' '.join([repr(i) for i in val])
            setattr(parseropts, self.dest(group), val)
            Option.set_value(self, confparser, parseropts, group)

    def __repr__(self):
        return 'ListOption<%s>' % (self.name)


class ConfigOption(ListOption):

    def __init__(self, name, short=(), long=(), default=VOID, help=VOID,
                 metavar=VOID, override=False):
        ListOption.__init__(self, name, validators.String, short, long, default,
                            help, metavar)
        self.override = override

    def process(self, parser, schema, config_opts, group):
        ListOption.process(self, parser, schema, config_opts, group)
        config_opts.append(self)

    def value(self, confparser, parseropts, group, ignore_errors):
        pass

    def set_value(self, confparser, parseropts, group):
        pass


class Config:
    """
    Dummy object that stores all the configuration data.
    """

    def __repr__(self):
        return 'Config(%r)' % self.__dict__


config = None

args = []

options = Options()


class LazyOptionParser(optparse.OptionParser):

    ignore_errors = False

    exit_status = 1

    def exit(self, status=0, msg=None):
        if self.ignore_errors:
            return
        optparse.OptionParser.exit(self, status, msg)

    def error(self, msg):
        if self.ignore_errors:
            return
        self.print_usage(sys.stderr)
        self.exit(self.exit_status, "%s: error: %s\n"
                  % (self.get_prog_name(), msg))

    def print_help(self, file=None):
        if self.ignore_errors:
            return
        optparse.OptionParser.print_help(self, file)

    def _process_short_opts(self, rargs, values):
        try:
            return optparse.OptionParser._process_short_opts(self, rargs,
                                                             values)
        except Exception, e:
            if not self.ignore_errors:
                raise

    def _process_long_opt(self, rargs, values):
        try:
            return optparse.OptionParser._process_long_opt(self, rargs, values)
        except Exception, e:
            if not self.ignore_errors:
                raise

    def _process_short_opts(self, rargs, values):
        try:
            return optparse.OptionParser._process_short_opts(self, rargs, values)
        except Exception, e:
            if not self.ignore_errors:
                raise


def load_options(version=None, description=None, ignore_errors=False):
    # load command-line options
    optparser = LazyOptionParser(version=version, description=description)
    optparser.ignore_errors = ignore_errors
    config_opts = options.process(optparser)
    (opts, args) = optparser.parse_args()
    log.debug('load_options() -> %r %r', opts, args)
    # help the GC
    optparser.destroy()
    return (opts, config_opts, args)


def make_config(values):
    log.debug('make_config()')
    config = Config()
    for (name, value) in values.items():
        if isinstance(value, dict):
            log.debug('make_config() -> processing group %s: %r', name, value)
            setattr(config, name, make_config(value))
        else:
            log.debug('make_config() -> processing value %s: %r', name, value)
            setattr(config, name, value)
    log.debug('make_config() -> config = %r', config)
    return config


def load_conf(config_file_paths, version, description, defaults, ignore_errors):
    log.debug('load_conf(%r, version=%r, description=%r, ignore_errors=%r)',
              config_file_paths, version, description, ignore_errors)
    global options

    # load command-line options
    (opts, config_opts, args) = load_options(version, description,
                                             ignore_errors=ignore_errors)

    # process config file options to see what config files to load
    for opt in config_opts:
        files = getattr(opts, opt.name)
        log.debug('load_conf() -> processing configuration file option '
                  '"%s": %r', opt.name, files)
        if not files:
            log.debug('load_conf() -> option not set! looking for the next')
            continue
        if opt.override:
            log.debug('load_conf() -> overriding default config files')
            config_file_paths = files
        else:
            log.debug('load_conf() -> appending to default config files')
            config_file_paths.extend(files)

    confparser = SafeConfigParser(defaults)
    readed = confparser.read(config_file_paths)
    log.debug('load_conf() -> readed config files: %r', readed)

    try:
        log.debug('load_conf() -> sections: %r', confparser.sections())
        log.debug('load_conf() -> readed values from config files: %r',
                  [confparser.items(s) for s in confparser.sections()])
        values = options.values(confparser, opts, ignore_errors)
    except InterpolationMissingOptionError, e:
        raise ConfigError('bad value substitution for option "%s" in '
                              'section [%s] (references an unexistent option '
                              '"%s")' % (e.option, e.section, e.reference))
    except InterpolationDepthError, e:
        raise ConfigError('value interpolation too deeply recursive in '
                          'option "%s", section [%s]' % (e.option, e.section))
    except InterpolationSyntaxError, e:
        raise ConfigError('bad syntax for interpolation variable in option '
                          '"%s", section [%s]' % (e.option, e.section))

    values = options.schema.to_python(values)
    log.debug('load_conf() -> validated values: %r', values)

    config = make_config(values)

    # TODO options.check_orphans(confparser, config)

    return (config, args)


def load_config(config_file_paths, version=None, description=None,
		add_plugin_opts=None, defaults=None):
    "callback signature: add_plugin_opts(config, args)"
    log.debug('load_config(%r, version=%r, description=%r, add_plugin_opts=%r)',
              config_file_paths, version, description, add_plugin_opts)
    global args
    global config

    (config, args) = load_conf(config_file_paths, version, description,
                               defaults, add_plugin_opts is not None)
    while add_plugin_opts:
        log.debug('load_config() -> calling %r', add_plugin_opts)
        add_plugin_opts = add_plugin_opts(config, args)
        log.debug('load_config() -> got config=%r / args=%r', config, args)
        (config, args) = load_conf(config_file_paths, version, description,
                                   defaults, add_plugin_opts is not None)

    return (config, args)


if __name__ == '__main__':

    import os
    import tempfile
    from formencode import validators as V

    logging.basicConfig(
        level   = logging.DEBUG,
        format  = '%(levelname)-8s %(message)s',
    )

    def print_config(config, prefix=''):
        for attr in dir(config):
            if not attr.startswith('__'):
                val = getattr(config, attr)
                if isinstance(val, Config):
                    print prefix, 'Group %s:' % attr
                    print_config(val, '\t')
                else:
                    print prefix, attr, '=', val

    options.init('pymind', 'Default group description', [
        Option('dry_run', V.StringBool, 'd', default=True,
                help="pretend, don't execute commands"),
        Option('bind_addr', V.CIDR, 'a', default='127.0.0.1', metavar='ADDR',
                help='IP address to bind to'),
        Option('bind_port', V.Int, 'p', default=9999, metavar='PORT',
                help="port to bind to"),
        Option('mandatory', V.Int, 'm', metavar='N',
                help="mandatory parameter"),
        ConfigOption('config_file', 'c', metavar="FILE",
                help="configuration file"),
        ConfigOption('override_config_file', 'o', metavar="FILE",
                help="configuration file", override=True),
        ListOption('plugins', V.String, 's', metavar="SERV", default=[],
                help="plugins pymin should use"),
        OptionGroup('test_grp', 'A test group', [
            Option('test', V.StringBool, default=False,
                    help="test group option"),
            Option('oneof', V.OneOf(['tcp', 'udp']), default='tcp',
                    help="test option for OneOf validator"),
            ListOption('list', V.StringBool, default=[True, True, False],
                    help="test ListOption"),
        ]),
    ])

    def add_more_plugin_opts(config, args):
        print 'add_more_plugin_opts'
        print '---------------'
        print config, args
        print '---------------'
        print
        g = options.get_group('plugin')
        g.add(ListOption('other', V.Int, default=[1,2], metavar='OTHER',
                         help="a list of numbers"))

    def add_plugin_opts(config, args):
        print 'add_plugin_opts'
        print '---------------'
        print config, args
        print '---------------'
        print
        if 'plugin' in config.plugins:
            options.add(
                OptionGroup('plugin', 'some plug-in options', [
                    Option('active', V.StringBool, default=True, metavar='ACT',
                            help="if ACT is true, the plug-in is active"),
                ])
            )
            return add_more_plugin_opts


    f = tempfile.NamedTemporaryFile()
    f.write("""
[pymind]
dry-run:         yes
bind-addr:       0.0.0.0
bind-port:       2000
log-config-file: /etc/pymin/log.conf

[test-grp]
test = yes
""")
    f.flush()
    f.seek(0)
    print '-'*78
    print f.read()
    print '-'*78

    try:
        (c, a) = load_config([f.name], '%prog 0.1', 'this is a program test',
                             add_plugin_opts)
        print "Config:"
        print_config(c)
        print "Args:", a
        print
        print "Globals:"
        print "Config:"
        print_config(config)
        print "Args:", args
    except ConfigError, e:
        print e
    except MissingSectionHeaderError, e:
        print "%s:%s: missing section header near: %s" \
                % (e.filename, e.lineno, e.line)
    except ParsingError, e:
        for (lineno, line) in e.errors:
            print "%s:%s: invalid syntax near: %s" % (e.filename, lineno, line)
        print e.errors
    except Invalid, e:
        print e.error_dict
    f.close()


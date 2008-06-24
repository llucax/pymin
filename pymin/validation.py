# vim: set encoding=utf-8 et sw=4 sts=4 :

import re
from formencode import Invalid
from formencode.validators import *
from formencode.compound import *

from pymin.item import Item
from pymin.validatedclass import Field


class UpOneOf(OneOf):
    """
    Same as :class:`OneOf` but values are uppercased before validation.

    Examples::

        >>> uoo = UpOneOf(['A', 'B', 'C'])
        >>> uoo.to_python('a')
        'A'
        >>> uoo.to_python('B')
        'B'
        >>> uoo.to_python('x')
        Traceback (most recent call last):
            ...
        Invalid: Value must be one of: A; B; C (not 'X')
    """

    def _to_python(self, value, state):
        return value.upper()


class HostName(FancyValidator):
    """
    Formencode validator to check whether a string is a correct host name

    Examples::

        >>> n = HostName()
        >>> n.to_python('host-name')
        'hostname'
        >>> n.to_python('host name')
        Traceback (most recent call last):
            ...
        Invalid: Not a valid host name
        >>> n.to_python('hostname' * 8)
        Traceback (most recent call last):
            ...
        Invalid: Host name is too long (maximum length is 63 characters)
    """

    messages = dict(
        empty = u'Please enter a host name',
        bad_format = u'Not a valid host name',
        too_long = u'Host name is too long (maximum length is '
                         u'%(max_len)d characters)',
    )

    max_len = 63 # official limit for a label
    hostnameRE = re.compile(r"^[a-zA-Z0-9][\w\-]*$")

    def validate_python(self, value, state):
        if len(value) > self.max_len:
            raise Invalid(self.message('host_too_long', state, value=value,
                                       max_len=self.max_len),
                          value, state)
        if not self.hostnameRE.search(value):
            raise Invalid(self.message('bad_format', state, value=value),
                          value, state)


class FullyQualifiedHostName(HostName):
    """
    Formencode validator to check whether a string is a correct host name

    Examples::

        >>> n = FullyQualifiedHostName()
        >>> n.to_python('example.com')
        'example.com'
        >>> n.to_python('example')
        Traceback (most recent call last):
            ...
        Invalid: Not a valid host name
        >>> n.to_python('example.' * 32 + 'com')
        Traceback (most recent call last):
            ...
        Invalid: Host name is too long (maximum length is 253 characters)
    """

    messages = dict(HostName._messages,
        empty = u'Please enter a fully qualified host name',
        bad_format = u'Not a fully qualified host name',
    )

    max_len = 253
    hostnameRE = re.compile(r"^[a-zA-Z0-9][\w\-\.]*\.[a-zA-Z]+$")


class IPAddress(FancyValidator):
    """
    Formencode validator to check whether a string is a correct IP address

    Examples::

        >>> ip = IPAddress()
        >>> ip.to_python('127.0.0.1')
        '127.0.0.1'
        >>> ip.to_python('299.0.0.1')
        Traceback (most recent call last):
            ...
        Invalid: The octets must be within the range of 0-255 (not '299')
        >>> ip.to_python('192.168.0.1/1')
        Traceback (most recent call last):
            ...
        Invalid: Please enter a valid IP address (a.b.c.d)
        >>> ip.to_python('asdf')
        Traceback (most recent call last):
            ...
        Invalid: Please enter a valid IP address (a.b.c.d)
    """
    messages = {
        'bad_format' : u'Please enter a valid IP address (a.b.c.d)',
        'illegal_octets' : u'The octets must be within the range of 0-255 (not %(octet)r)',
    }

    def validate_python(self, value, state):
        try:
            octets = value.split('.')

            # Only 4 octets?
            if len(octets) != 4:
                raise Invalid(self.message("bad_format", state, value=value), value, state)

            # Correct octets?
            for octet in octets:
                if int(octet) < 0 or int(octet) > 255:
                    raise Invalid(self.message("illegal_octets", state, octet=octet), value, state)

        # Splitting faild: wrong syntax
        except ValueError:
            raise Invalid(self.message("bad_format", state), value, state)



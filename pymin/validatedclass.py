# vim: set et sts=4 sw=4 encoding=utf-8 :

r"""Validated classes constructed with declarative style.

This is a black magic module to ease the creation of classes that get
their attributes validated using formencode validators at creation time
(providing a constructor) and when updating (via a provided update
method).

The important classes of this module are Field and ValidatedClass. When
you'd like a class to validate their attributes, just inherit from
ValidatedClass and declare all the attributes it will have as class
attributes using Field instances. For example:

>>> import formencode
>>> class Test(ValidatedClass):
>>>     name = Field(formencode.validators.String(not_empty=True))
>>>     age = Field(formencode.validators.Int(max=110, if_empty=None,
>>>                                                    if_missing=None))
>>>     # Some global validation after individual fields validation
>>>     # (use pre_validator to validate *before* the individual fields
>>>     # validation)
>>>     def chained_validator(self, fields, state):
>>>         if 'Jr' in fields['name'] and fields['age'] > 25:
>>>             raise formencode.Invalid(u"Junior can't be older than 25 years",
>>>                                     fields, state, error_dict=dict(
>>>                                         age='Should not be more than 25'))
>>> try:
>>>     # Will fail because 'name' is mandatory
>>>     t = Test()
>>>     assert 'It should raised' is False
>>> except formencode.Invalid, e:
>>>     print unicode(e), e.error_dict
>>> t = Test(name='Graham') # Keyword arguments are valid
>>> assert t.name == 'Graham'
>>> t = Test('Graham') # But can be used without keywords too!
>>>                    # Use the order of fields declaration
>>> assert t.name == 'Graham'
>>> t = Test('Graham', 20)
>>> assert t.name == 'Graham' and t.age == 20
>>> t.update('Graham Jr.') # An update method is provided
>>> assert t.name == 'Graham Jr.'
>>> t.update(age=18) # And accepts keyword arguments too
>>> assert t.age == 18
>>> # Updates are validated
>>> try:
>>>     # Will fail because Junior can't be older than 25 years
>>>     t.update(age=40)
>>>     assert 'It should raised' is False
>>> except formencode.Invalid, e:
>>>     print unicode(e), e.error_dict
>>> # Other operations are not
>>> t.age = 50
>>> assert t.age == 50
>>> # But you can use an empty update to validate
>>> try:
>>>     # Will fail because Junior can't be older than 25 years
>>>     t.update()
>>>     assert 'It should raised' is False
>>> except formencode.Invalid, e:
>>>     print unicode(e), e.error_dict
>>> # You can use the alias validate() too
>>> try:
>>>     # Will fail because Junior can't be older than 25 years
>>>     t.validate()
>>>     assert 'It should raised' is False
>>> except formencode.Invalid, e:
>>>     print unicode(e), e.error_dict

Nice, ugh?
"""

__all__ = ('Field', 'ValidatedClass')

from formencode import Invalid
from formencode.schema import Schema
from formencode.validators import FancyValidator

# FIXME not thread safe (use threadlocal?)
# This is a counter to preserve the order of declaration of fields (class
# attributes). When a new Field is instantiated, the Field stores internally
# the current counter value and increments the counter, so then, when doing
# the metaclass magic, you can know the order in which the fields were declared
declarative_count = 0

class Field(object):
    r"""Field(validator[, doc]) -> Field object

    This is a object used to declare class attributes that will be validated.
    The only purpose of this class is declaration. After a Field is declared,
    the metaclass process it and remove it, leaving the attributes as regular
    objects.

    validator - A field validator. You can use any formencode validator.
    doc - Document string (not used yet)

    See module documentation for examples of usage.
    """
    def __init__(self, validator, doc=None):
        r"Initialize the object, see the class documentation for details."
        self.validator = validator
        self.doc = doc
        # Set and update the declarative counter
        global declarative_count
        self._declarative_count = declarative_count
        declarative_count += 1

class ValidatedMetaclass(type):
    r"""ValidatedMetaclass(classname, bases, class_dict) -> type

    This metaclass does the magic behind the scenes. It inspects the class
    for Field instances, using them to build a validator schema and replacing
    them with regular objects (None by default). It looks for pre_validator
    and chained_validator attributes (assuming they are methods), and builds
    a simple FancyValidator to add them as pre and chained validators to the
    schema.

    This metaclass add this attributes to the class:
        class_validator - Schema validator for the class
        validated_fields - Tuple of declared class fields (preserving order)

    And remove this attributes (if present):
        pre_validator - Provided pre validator, added to the class_validator
        chained_validator - Provided chained validator, added too

    This metaclass should be used indirectly inheriting from ValidatedClass.
    """
    def __new__(meta, classname, bases, class_dict):
        # Reset the declarative_count so we can order again the fields
        # (this is not extrictly necessary, it's just to avoid the counter
        # to go too high)
        global declarative_count
        declarative_count = 0
        # List of attributes that are Fields
        fields = [(k, v) for k, v in class_dict.items() if isinstance(v, Field)]
        # Sort them according to the declarative counter
        fields.sort(key=lambda i: i[1]._declarative_count)
        # Validated fields to preserve field order for constructor
        validated_fields = list()
        # Create a new validator schema for the new class
        schema = Schema()
        for name, field in fields:
            validated_fields.append(name)
            # We don't want the class attribute to be a Field
            class_dict[name] = None
            # But we want its validator to go into the schema
            schema.add_field(name, field.validator)
        # Check if the class has a pre and/or chained validators to check if
        # the class is valid as a whole before/after (respectively) validating
        # each individual field
        for key, add_to_schema in (('pre_validator', schema.add_pre_validator),
                        ('chained_validator', schema.add_chained_validator)):
            if key in class_dict:
                # Create a simple fancy validator
                class Validator(FancyValidator):
                    validate_python = class_dict[key]
                # And add it to the schema's special validators
                add_to_schema(Validator)
                # We don't need the validator in the class anymore
                del class_dict[key]
        # Now we add the special new attributes to the new class
        class_dict['validated_fields'] = tuple(validated_fields)
        class_dict['class_validator'] = schema
        return type.__new__(meta, classname, bases, class_dict)

def join_args(args, names, kwargs):
    r"""join_args(args, names, kwargs) -> dict

    This is a helper function to join positional arguments ('args') to keyword
    arguments ('kwargs'). This is done using the 'names' list, which maps
    positional arguments indexes to keywords. It *modifies* kwargs to add the
    positional arguments using the mapped keywords (and checking for
    duplicates). The number of argument passed is checked too (it should't be
    greater than len(names). Extra keywords are not checked though, because it
    assumes the validator schema takes care of that.

    args - Positional arguments.
    names - list of keywords.
    kwargs - Keywords arguments.
    """
    if len(args) > len(names):
        raise Invalid('Too many arguments', args, None)
    for i in range(len(args)):
        if names[i] in kwargs:
            raise Invalid("Duplicated value for argument '%s'" % names[i],
                                    kwargs[names[i]], None)
        kwargs[names[i]] = args[i]
    return kwargs

class ValidatedClass(object):
    r"""ValidatedClass(*args, **kw) -> ValidatedClass object

    You should inherit your classes from this one, declaring the class
    attributes using the Field class to specify a validator for each
    attribute.

    Please see the module documentation for details and examples of usage.
    """

    __metaclass__ = ValidatedMetaclass

    def __init__(self, *args, **kw):
        r"Initialize and validate the object, see the class documentation."
        for name in self.validated_fields:
            # Create all the attributes
            setattr(self, name, None)
        # Update the attributes with the arguments passed
        self.update(**join_args(args, self.validated_fields, kw))

    def update(self, *args, **kw):
        r"update(*args, **kw) - Update objects attributes validating them."
        # Get class attributes as a dict
        attrs = dict([(k, getattr(self, k)) for k in self.validated_fields])
        # Update the dict with the arguments passed
        attrs.update(join_args(args, self.validated_fields, kw))
        # Validate the resulting dict
        attrs = self.class_validator.to_python(attrs)
        # If we are here, there were no errors, so update the real attributes
        for k, v in attrs.items():
            setattr(self, k, v)

    def validate(self):
        r"validate() - Validate the object's attributes."
        self.update()


if __name__ == '__main__':

    import formencode

    class Test(ValidatedClass):
        name = Field(formencode.validators.String(not_empty=True))
        age = Field(formencode.validators.Int(max=110, if_empty=None,
                                                       if_missing=None))
        # Some global validation after individual fields validation
        def chained_validator(self, fields, state):
            if 'Jr' in fields['name'] and fields['age'] > 25:
                raise formencode.Invalid(u"Junior can't be older than 25 years",
                                        fields, state, error_dict=dict(
                                            age='Should not be more than 25'))

    try:
        # Will fail because 'name' is mandatory
        t = Test()
        assert 'It should raised' is False
    except formencode.Invalid, e:
        print unicode(e), e.error_dict

    t = Test(name='Graham') # Keyword arguments are valid
    assert t.name == 'Graham'

    t = Test('Graham') # But can be used without keywords too!
                       # Use the order of fields declaration
    assert t.name == 'Graham'

    t = Test('Graham', 20)
    assert t.name == 'Graham' and t.age == 20

    t.update('Graham Jr.') # An update method is provided
    assert t.name == 'Graham Jr.'

    t.update(age=18) # And accepts keyword arguments too
    assert t.age == 18

    # Updates are validated
    try:
        # Will fail because Junior can't be older than 25 years
        t.update(age=40)
        assert 'It should raised' is False
    except formencode.Invalid, e:
        print unicode(e), e.error_dict

    # Other operations are not
    t.age = 50
    assert t.age == 50

    # But you can use an empty update to validate
    try:
        # Will fail because Junior can't be older than 25 years
        t.update()
        assert 'It should raised' is False
    except formencode.Invalid, e:
        print unicode(e), e.error_dict

    # You can use the alias validate() too
    try:
        # Will fail because Junior can't be older than 25 years
        t.validate()
        assert 'It should raised' is False
    except formencode.Invalid, e:
        print unicode(e), e.error_dict



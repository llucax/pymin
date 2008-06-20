# vim: set encoding=utf-8 et sw=4 sts=4 :

import crypt

from pymin.seqtools import Sequence
from pymin.service.util import DictSubHandler

__all__ = ('UserHandler',)


class User(Sequence):
    def __init__(self, name, password):
        self.name = name
        self.password = crypt.crypt(password,'BA')
    def as_tuple(self):
        return (self.name, self.password)
    def update(self, password=None):
        if password is not None:
            self.password = crypt.crypt(password,'BA')

class UserHandler(DictSubHandler):

    handler_help = u"Manage proxy users"

    _cont_subhandler_attr = 'users'
    _cont_subhandler_class = User


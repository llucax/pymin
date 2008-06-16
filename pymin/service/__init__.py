# vim: set encoding=utf-8 et sw=4 sts=4 :

import imp
import logging ; log = logging.getLogger('pymin.service')

class LoadError(ImportError):
    pass

def load_service(name, search_paths):
    log.debug('load_service(%s, %r)', name, search_paths)
    try:
        (fp, path, desc) = imp.find_module(name, search_paths)
    except ImportError:
        raise LoadError('module "%s" not found' % name)

    log.debug('load_service() -> find_module() returned %r', (fp, path, desc))
    try:
        m = imp.load_module(name, fp, path, desc)
        log.debug('load_service() -> loaded module %r', m)
        return imp.load_module(name, fp, path, desc)
    finally:
        if fp:
            fp.close()


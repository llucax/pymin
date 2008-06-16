# vim: set encoding=utf-8 et sw=4 sts=4 :

import imp

class LoadError(ImportError):
    pass

def load_service(name, search_paths):
    try:
        (fp, path, desc) = imp.find_module(name, search_paths)
    except ImportError:
        raise LoadError('module "%s" not found' % name)

    try:
        return imp.load_module(name, fp, path, desc)
    finally:
        if fp:
            fp.close()


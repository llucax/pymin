# vim: set encoding=utf-8 et sw=4 sts=4 :

import os
import errno
import signal
import subprocess
import logging ; log = logging.getLogger('pymin.procman')

__all__ = ('ProcessManager', 'manager', 'register', 'unregister', 'once',
           'start', 'stop', 'restart', 'kill', 'get', 'has', 'sigchild_handler')

class ProcessInfo:
    def __init__(self, name, command, callback=None, persist=False,
                 max_errors=3, args=None, kwargs=None):
        self._name = name
        self.command = command
        self.callback = callback
        if args is None: args = list()
        self.args = args
        if kwargs is None: kwargs = dict()
        self.kwargs = kwargs
        self.persist = persist
        self.max_errors = max_errors
        self.clear()
    def clear(self):
        self._dont_run = False
        self._signal = None
        self._process = None
        self._error_count = 0
    def start(self):
        assert self.process is None
        self.restart()
    def restart(self):
        self.clear()
        log.debug(u'ProcessInfo.restart(): executing %s', self.command)
        self._process = subprocess.Popen(self.command,
                                         *self.args, **self.kwargs)
    def stop(self):
        assert self.process is not None
        self._dont_run = True
        if self._signal == signal.SIGTERM or self._signal == signal.SIGKILL:
            # Allready stopped, kill it
            self.kill(signal.SIGKILL)
        else:
            # Stop it
            self.kill(signal.SIGTERM)
    def kill(self, signum):
        log.debug(u'ProcessInfo.kill(): killing pid %s with signal %s',
                      self.process.pid, signum)
        assert self.process is not None
        os.kill(self.process.pid, signum)
        self._signal = signum
    @property
    def running(self):
        return self.process is not None and self.process.poll() is None
    @property
    def name(self):
        return self._name
    @property
    def process(self):
        return self._process
    @property
    def error_count(self):
        return self._error_count
    def __repr__(self):
        pid = None
        if self.process is not None:
            pid = self.process.pid
        return 'ProcessInfo(name=%s, pid=%s command=%s, persist=%s, cb=%s)' % (
                    self.name, pid, self.command, self.persist,
                    self.callback and self.callback.__name__ or None)

class ProcessManager:

    def __init__(self):
        self.services = dict()
        self.namemap = dict()
        self.pidmap = dict()
        log.debug(u'ProcessManager()')

    def register(self, name, command=None, callback=None, persist=False,
                max_errors=3, *args, **kwargs):
        log.debug(u'ProcessManager.register(%s, %s, %s, %s, %s, %s, %s)',
                  name, command, callback, persist, max_errors, args, kwargs)
        if not isinstance(name, ProcessInfo):
            pi = ProcessInfo(name, command, callback, persist, max_errors,
                             args, kwargs)
        else:
            pi = name
            name = pi.name
        assert not self.has(name)
        self.services[name] = pi
        return pi

    def unregister(self, name):
        log.debug(u'ProcessManager.unregister(%s)', name)
        if isinstance(name, ProcessInfo):
            pi = name
            name = pi.name
        else:
            pi = self.services[name]
        del self.services[name]
        return pi

    def _call(self, pi):
        pi.start()
        self.namemap[pi.name] = self.pidmap[pi.process.pid] = pi

    def once(self, name, command=None, callback=None, persist=False,
                max_errors=3, *args, **kwargs):
        log.debug(u'ProcessManager.once(%s, %s, %s, %s, %s, %s, %s)',
                  name, command, callback, persist, max_errors, args, kwargs)
        if not isinstance(name, ProcessInfo):
            pi = ProcessInfo(name, command, callback, persist, max_errors,
                             args, kwargs)
        else:
            pi = name
            name = pi.name
        assert not self.has(name)
        self._call(pi)
        return pi

    def start(self, name):
        log.debug(u'ProcessManager.start(%s)', name)
        if isinstance(name, ProcessInfo):
            name = name.name
        if name not in self.namemap:
            self._call(self.services[name])
            return True
        return False

    def stop(self, name):
        log.debug(u'ProcessManager.stop(%s)', name)
        if isinstance(name, ProcessInfo):
            name = name.name
        if name in self.namemap:
            self.namemap[name].stop()
            return True
        return False

    def restart(self, name):
        log.debug(u'ProcessManager.restart(%s)', name)
        if isinstance(name, ProcessInfo):
            name = name.name
        # we have to check first in namemap in case is an unregistered
        # process (added with once())
        if name in self.namemap:
            pi = self.namemap[name]
            # the process will change its PID, so we delete it while we know it
            del self.pidmap[pi.process.pid]
            pi.stop()
            pi.process.wait()
            pi.restart()
            # add the new PID
            self.pidmap[pi.process.pid] = pi
            return True
        else:
            self.start(name)
            return False

    def kill(self, name, signum):
        log.debug(u'ProcessManager.kill(%s, %s)', name, signum)
        if isinstance(name, ProcessInfo):
            name = name.name
        if name in self.namemap:
            self.namemap[name].kill(name, stop)
            return True
        return False

    def sigchild_handler(self, signum, stack_frame=None):
        log.debug(u'ProcessManager.sigchild_handler(%s)', signum)
        try:
            (pid, status) = os.waitpid(-1, os.WNOHANG)
        except OSError, e:
            log.debug(u'ProcessManager.sigchild_handler(): OSError')
            if e.errno is errno.ECHILD:
                log.debug(u'ProcessManager.sigchild_handler(): OSError ECHILD')
                return
            raise
        log.debug(u'ProcessManager.sigchild_handler: pid=%s, status=%s',
                      pid, status)
        while pid:
            if pid in self.pidmap:
                p = self.pidmap[pid]
                p.process.returncode = status
                if p.callback is not None:
                    log.debug(u'ProcessManager.sigchild_handler: '
                                  u'calling %s(%s)', p.callback.__name__, p)
                    p.callback(self, p)
                if (p._dont_run or not p.persist
                                or p._error_count >= p.max_errors):
                    log.debug(u"ProcessManager.sigchild_handler: can't "
                            u'persist, dont_run=%s, persist=%s, error_cout=%s, '
                            u'max_errors=%s', p._dont_run, p.persist,
                            p._error_count, p.max_errors)
                    del self.namemap[p.name]
                    del self.pidmap[pid]
                    p.clear()
                else:
                    log.debug(u'ProcessManager.sigchild_handler: persist')
                    if p.process.returncode == 0:
                        p._error_count = 0
                        log.debug(u'ProcessManager.sigchild_handler: '
                                u'return OK, resetting error_count')
                    else:
                        p._error_count += 1
                        log.debug(u'ProcessManager.sigchild_handler: return'
                                u'not 0, error_count + 1 = %s', p._error_count)
                    del self.pidmap[pid]
                    p.restart()
                    self.pidmap[p.process.pid] = p
            try:
                (pid, status) = os.waitpid(-1, os.WNOHANG)
            except OSError, e:
                if e.errno == errno.ECHILD:
                    return
                raise

    def get(self, name):
        if isinstance(name, basestring): # is a name
            if name in self.namemap:
                return self.namemap[name]
            if name in self.services:
                return self.services[name]
        else: # is a pid
            if name in self.pidmap:
                return self.pidmap[name]
        raise KeyError, name
    # Syntax sugar for self[name]
    __getitem__ = get

    def has(self, name):
        if isinstance(name, basestring): # is a name
            if name in self.namemap:
                return True
            if name in self.services:
                return True
        else: # is a pid
            if name in self.pidmap:
                return True
        return False
    # Syntax sugar for name in self
    __contains__ = has


if __name__ == '__main__':
    logging.basicConfig(
        level   = logging.DEBUG,
        format  = '%(asctime)s %(levelname)-8s %(message)s',
        datefmt = '%H:%M:%S',
    )


# Globals
manager = ProcessManager()
register = manager.register
unregister = manager.unregister
once = manager.once
start = manager.start
stop = manager.stop
restart = manager.restart
kill = manager.kill
get = manager.get
has = manager.has
sigchild_handler = manager.sigchild_handler


if __name__ == '__main__':

    import signal
    import time

    sig = None
    count = 0

    def SIGCHLD_handler(signum, stacktrace):
        global sig
        sig = signum
        print 'SIGCHLD', signum

    def notify(pm, pi):
        global count
        if pi.name == 'test-service':
            print 'test-service count =', count
            count += 1
            if count > 4:
                print 'set test-service non-persistent, start test-service-2'
                pi.persist = False
                assert 'test-service-2' not in manager.namemap
                pm.start('test-service-2')
                assert 'test-service-2' in manager.namemap
                assert get('test-service-2').running
        print 'died:', pi.name, pi.command

    register('test-service', ('sleep', '2'), notify, True)
    assert 'test-service' in manager.services
    assert 'test-service' not in manager.namemap
    assert not get('test-service').running
    assert manager['test-service'] == get('test-service')
    assert has('test-service')
    assert 'test-service' in manager

    register('test-service-2', ('sleep', '3'), notify, False)
    assert 'test-service-2' in manager.services
    assert 'test-service-2' not in manager.namemap
    assert not get('test-service-2').running

    signal.signal(signal.SIGCHLD, SIGCHLD_handler)

    once('test-once', ('sleep', '5'), notify)
    assert 'test-once' not in manager.services
    assert 'test-once' in manager.namemap
    assert get('test-once').running
    assert get('test-once').process.pid
    pid = get('test-once').process.pid
    restart('test-once')
    assert pid != get('test-once').process.pid
    assert pid != manager.pidmap[get('test-once').process.pid].process.pid

    start('test-service')
    assert 'test-service' in manager.namemap
    assert get('test-service').running
    assert get('test-service').process.pid
    pid = get('test-service').process.pid
    restart('test-service')
    assert pid != get('test-service').process.pid
    assert pid != manager.pidmap[get('test-service').process.pid].process.pid

    print "Known processes:", manager.services.keys()
    print "Waiting...", manager.namemap.keys()
    print "------------------------------------------------------------------"
    while manager.pidmap:
        signal.pause()
        if sig == signal.SIGCHLD:
            sigchild_handler(sig)
            sig = None
        print "Known processes:", manager.services.keys()
        print "Waiting...", manager.namemap.keys()
        print "------------------------------------------------------------------"
    assert 'test-service' not in manager.namemap
    assert 'test-service-2' not in manager.namemap
    assert 'test-once' not in manager.services
    assert 'test-once' not in manager.namemap

    restart('test-service')
    assert get('test-service').process.pid
    assert manager.pidmap[get('test-service').process.pid].process.pid

    once('test-wait', ('sleep', '2'))
    print 'test-wait running?', get('test-wait').running
    assert get('test-wait').running
    print 'Waiting test-wait to return...'
    ret = get('test-wait').process.wait()
    print 'Done! returned:', ret


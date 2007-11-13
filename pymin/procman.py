# vim: set encoding=utf-8 et sw=4 sts=4 :

import os
import errno
import signal
import subprocess

__ALL__ = ('ProcessManager', 'manager', 'register', 'unregister', 'call',
           'start', 'stop', 'kill', 'get', 'has', 'sigchild_handler')

class ProcessInfo:
    def __init__(self, name, command, callback=None, persist=False,
                       args=None, kw=None, max_errors=3):
        self.name = name
        self.command = command
        self.callback = callback
        if args is None: args = list()
        self.args = args
        if kw is None: kw = dict()
        self.kw = kw
        self.persist = persist
        self.max_errors = max_errors
        self.clear()
    def clear(self):
        self.dont_run = False
        self.signal = None
        self.process = None
        self.error_count = 0
        self.last_return = None
        self.running = False
    def start(self):
        assert self.process is None
        self.restart()
    def restart(self):
        self.clear()
        self.process = subprocess.Popen(self.command, *self.args, **self.kw)
        self.running = True
    def stop(self):
        assert self.process is not None
        self.dont_run = True
        if self.signal == signal.SIGTERM or self.signal == signal.SIGKILL:
            # Allready stopped, kill it
            self.kill(signal.SIGKILL)
        else:
            # Stop it
            self.kill(signal.SIGTERM)
    def kill(self, signum):
        assert self.process is not None
        os.kill(pi.process.pid, signum)
        self.signal = signum
    def __repr__(self):
        pid = None
        if self.process is not None:
            pid = self.process.pid
        return 'ProcessInfo(name=%s, pid=%s command=%s, persist=%s, cb=%s)' % (
                    self.name, pid, self.command, self.persist,
                    self.callback.__name__)

class ProcessManager:

    def __init__(self):
        self.services = dict()
        self.namemap = dict()
        self.pidmap = dict()

    def register(self, name, command, callback=None, persist=False,
                       *args, **kw):
        self.services[name] = ProcessInfo(name, command, callback, persist,
                                          args, kw)

    def unregister(self, name):
        del self.services[name]

    def _call(self, pi):
        pi.start()
        self.namemap[pi.name] = self.pidmap[pi.process.pid] = pi

    def call(self, name, command, callback=None, persist=False, *args, **kw):
        pi = ProcessInfo(name, command, callback, persist, args, kw)
        self._call(pi)

    def start(self, name):
        assert name not in self.namemap
        self._call(self.services[name])

    def stop(self, name):
        assert name in self.namemap
        self.namemap[name].stop(name)

    def kill(self, name, signum):
        assert name in self.namemap
        self.namemap[name].kill(name, stop)

    def sigchild_handler(self, signum, stack_frame=None):
        try:
            (pid, status) = os.waitpid(-1, os.WNOHANG)
        except OSError, e:
            if e.errno is e.ECHILD:
                return
            raise
        while pid:
            if pid in self.pidmap:
                p = self.pidmap[pid]
                if p.callback is not None:
                    p.callback(self, p)
                if p.dont_run or not p.persist or p.error_count >= p.max_errors:
                    del self.namemap[p.name]
                    del self.pidmap[pid]
                    p.clear()
                else:
                    if p.process.returncode == 0:
                        p.error_count = 0
                    else:
                        p.error_count += 1
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
        return KeyError, name

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

    def __getitem__(self, name):
        return self.get(name)

    def __contains__(self, name):
        return self.has(name)

# Globals
manager = ProcessManager()
register = manager.register
unregister = manager.unregister
call = manager.call
start = manager.start
stop = manager.stop
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
                print 'test-service not persistent anymore, start test2'
                pi.persist = False
                pm.start('test2')
        print 'died:', pi.name, pi.command

    register('test-service', ('sleep', '2'), notify, True)
    register('test2', ('sleep', '3'), notify, False)

    signal.signal(signal.SIGCHLD, SIGCHLD_handler)

    call('test', ('sleep', '5'), notify)
    start('test-service')

    print "Esperando...", [pi.name for pi in manager.namemap.values()]
    while manager.pidmap:
        signal.pause()
        if sig == signal.SIGCHLD:
            sig = None
            sigchild_handler(sig)
        print "Esperando...", [pi.name for pi in manager.namemap.values()]


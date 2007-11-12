# vim: set encoding=utf-8 et sw=4 sts=4 :

import os
import errno
import subprocess

class ProcessInfo:
    def __init__(self, name, process, args, kw, callback=None, persist=False):
        self.name = name
        self.process = process
        self.args = args
        self.kw = kw
        self.callback = callback
        self.persist = persist
    def __repr__(self):
        return 'ProcessInfo(name=%s, pid=%s, persist=%s, cb=%s, args=%s)' % (
                    self.name, self.process.pid, self.persist,
                    self.callback.__name__, self.args)

class ProcessManager:

    def __init__(self):
        self.namemap = dict()
        self.pidmap = dict()

    def call(self, name, callback, persist, *args, **kw):
        proc = subprocess.Popen(*args, **kw)
        procinfo = ProcessInfo(name, proc, args, kw, callback, persist)
        self.namemap[name] = self.pidmap[proc.pid] = procinfo

    def sigchild_handler(self, signum):
        try:
            (pid, status) = os.waitpid(-1, os.WNOHANG)
        except OSError, e:
            if e.errno is e.ECHILD:
                return
            raise
        while pid:
            if pid in self.pidmap:
                p = self.pidmap[pid]
                del self.namemap[p.name]
                del self.pidmap[pid]
                if p.callback is not None:
                    p.callback(p)
                if p.persist:
                    self.call(p.name, p.callback, True, *p.args, **p.kw)
            try:
                (pid, status) = os.waitpid(-1, os.WNOHANG)
            except OSError, e:
                if e.errno == errno.ECHILD:
                    return
                raise

    def __getitem__(self, name):
        if isinstance(name, basestring): # is a name
            return self.namemap[name]
        else: # is a pid
            return self.pidmap[name]

    def __contains__(self, name):
        if isinstance(name, basestring): # is a name
            return name in self.namemap
        else: # is a pid
            return name in self.pidmap


if __name__ == '__main__':

    import signal
    import time

    sig = None

    def sigchild_handler(signum, stacktrace):
        global sig
        sig = signum
        print 'SIGCHLD', signum

    def test_notify(proc):
        print 'test died:', proc, proc.name, proc.process.pid

    procman = ProcessManager()

    signal.signal(signal.SIGCHLD, sigchild_handler)

    procman.call('test', test_notify, True, ('sleep', '5'))

    while True:
        time.sleep(1)
        print "Esperando...",
        if 'test' in procman:
            print procman['test']
        else:
            print
        if sig == signal.SIGCHLD:
            sig = None
            procman.sigchild_handler(sig)


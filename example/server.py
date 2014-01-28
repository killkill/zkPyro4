#!/bin/env python
# -*- coding: UTF-8 -*-

import Pyro4
from zkPyroClient import zkPyroClient

class Thing(object):
    def method(self, arg):
        print "call this one"
        return arg*2

'''
# ------ normal code ------
daemon = Pyro4.Daemon()
uri = daemon.register(Thing())
ns = Pyro4.locateNS()
ns.register("mythingy", uri)
daemon.requestLoop()

# ------ alternatively, using serveSimple -----
Pyro4.Daemon.serveSimple(
    {
        Thing(): "mythingy"
    },
    ns=True, verbose=True)
'''

zk = zkPyroClient()
zk.register("test", Thing())
zk.requestLoop()

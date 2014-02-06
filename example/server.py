#!/bin/env python
# -*- coding: UTF-8 -*-

import zkPyro4


class Thing(object):
    def __init__(self):
        pass

    def method(self, arg):
        print "call this  method"
        return int(arg)

    def call(self,arg):
        print "call this  call"
        return [
            {"a":"a","b":"b"},
             {"a":"a","b":"b"},
              {"a":"a","b":"b"},
        ]

    @property
    def prop(self):
        return __name__

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

zk = zkPyro4.locateNS()
zk.register("test", Thing())
print "service running!"
zk.requestLoop()

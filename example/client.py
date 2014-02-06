#!/bin/env python
# -*- coding: UTF-8 -*-

import traceback
import zkPyro4

zk = zkPyro4.locateNS()

for i in range(1, 100000):
    a = raw_input(">>> ")
    print "input a: "+a
    try:
        thing = zk.lookup("test")
    except:
        traceback.print_exc()
    try:
        if len(a) > 0:
            print "methord:%s"%(thing.method(10))
        else:
            print "call:%s"%(thing.call(10))
    except:
        traceback.print_exc()





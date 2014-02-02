#!/bin/env python
# -*- coding: UTF-8 -*-

from zkPyroClient import zkPyroClient
import traceback
zk = zkPyroClient()
for i in range(1, 100000):
    raw_input(">>> ")
    try:
        thing = zk.lookup("test")
    except:
        traceback.print_exc()
    try:
        print thing.method(10)
        print thing.zkPyro4_echo__(10)
    except:
        traceback.print_exc()

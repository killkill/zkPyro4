#!/bin/env python
# -*- coding: UTF-8 -*-

from zkPyroClient import zkPyroClient
zk = zkPyroClient()
thing = zk.lookup("test")
print thing.method(42)   # prints 84
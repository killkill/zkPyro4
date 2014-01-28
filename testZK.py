#!/bin/env python
# -*- coding: UTF-8 -*-

from kazoo.client import KazooClient
from kazoo.exceptions import *
import traceback
zk = KazooClient(hosts='127.0.0.1:2181')
zk.start()
# children = zk.get_children('/')
print "zk version:" + (".".join(str(x) for x in zk.server_version()))
print "client id :" + str(zk.client_id[0])
servicePath = "/{root}/{service}/provider".format(root="zkpyro", service="serviceName01")
nodeId = zk.client_id[0]
nodePath = "{servicePath}/{node}".format(servicePath=servicePath, node=nodeId)
print "servicePath:" + servicePath
try:
    zk.create(nodePath, ephemeral=True, makepath=True)
    zk.set(nodePath, "pyro.url")
    print "Znode value:" + zk.get(nodePath)[0]
except NodeExistsError:
    traceback.print_stack()
zk.stop()
#!/bin/env python
# -*- coding: UTF-8 -*-

from kazoo.client import KazooClient
from kazoo.exceptions import *
import traceback
import Pyro4
import random

class zkPyroClient(object):
    def __init__(self,hosts='127.0.0.1:2181',
                 timeout=10.0, client_id=None, handler=None,
                 default_acl=None, auth_data=None, read_only=None,
                 randomize_hosts=True, connection_retry=None,
                 command_retry=None, logger=None, **kwargs):
        self.zk = KazooClient(hosts=hosts,
                     timeout=timeout, client_id=client_id, handler=handler,
                     default_acl=default_acl, auth_data=auth_data, read_only=read_only,
                     randomize_hosts=randomize_hosts, connection_retry=connection_retry,
                     command_retry=command_retry, logger=logger, **kwargs)
        self.zk.start()
        self.daemon = Pyro4.Daemon()
        self.nodeId = self.zk.client_id[0]

    def getServicePath(self, name, root="zkpyro"):
        return "/{root}/{service}".format(root=root, service=name)

    def register(self, name, obj):
        uri = self.daemon.register(obj)
        servicePath = self.getServicePath(name)
        nodePath = "{servicePath}/provider/{node}".format(servicePath=servicePath, node=self.nodeId)
        try:
            self.zk.create(nodePath, ephemeral=True, makepath=True)
            self.zk.set(nodePath, str(uri))
        except NodeExistsError:
            traceback.print_stack()

    def requestLoop(self):
        self.daemon.requestLoop()

    def lookup(self, name):
        servicePath = self.getServicePath(name)
        nodePath = "{servicePath}/consumer/{node}".format(servicePath=servicePath, node=self.nodeId)
        providerPath = "{servicePath}/provider/".format(servicePath=servicePath)
        try:
            self.zk.create(nodePath, ephemeral=True, makepath=True)
            nodes = self.zk.get_children(providerPath, include_data=False)
            if len(nodes) == 0:
                raise Exception("No more service(%s) Provider node"%name)
            else:
                print nodes
                random.shuffle(nodes)
                node = nodes[0]
                uri = self.zk.get("{providerPath}/{node}".format(providerPath=providerPath, node=node))[0]
                print uri
            return Pyro4.Proxy(uri)
        except NodeExistsError:
            traceback.print_stack()

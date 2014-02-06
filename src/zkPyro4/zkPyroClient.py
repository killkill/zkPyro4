#!/bin/env python
# -*- coding: UTF-8 -*-

from kazoo.client import KazooClient
from kazoo.retry import KazooRetry
from kazoo.exceptions import *
import traceback
import Pyro4
import random
from kazoo.client import KazooState
import threading
import logging
import signal

from zkPyro4.Exceptions import NoMoreServiceProviderException


class zkPyroClient(object):
    def __init__(self, hosts='127.0.0.1:2181',
                 timeout=10.0, client_id=None, handler=None,
                 default_acl=None, auth_data=None, read_only=None,
                 randomize_hosts=True, connection_retry=None,
                 command_retry=None, logger=None, root="zkpyro", **kwargs):
        if logger is None:
            self.logger = logging.getLogger(__name__)
            self.logger.setLevel(logging.DEBUG)
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)
        else:
            self.logger = logger

        self.zk = KazooClient(hosts=hosts,
                     timeout=timeout, client_id=client_id, handler=handler,
                     default_acl=default_acl, auth_data=auth_data, read_only=read_only,
                     randomize_hosts=randomize_hosts, connection_retry=connection_retry or KazooRetry(max_tries=999999999,delay=1,interrupt=self.zkConnectionReady),
                     command_retry=command_retry, logger=None, **kwargs)

        self.zk.start(timeout=3)
        self.daemon = Pyro4.Daemon()
        self._selectNodeCounter = 0
        self._firstLookup = True
        self.watchedServices = set()
        self.root = root
        self.serviceCache = {}
        self.zk.add_listener(self.zkConnectionListener)
        self.registerDict = {}
        self.stopEvent = threading.Event()
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)
        # todo:I don`t know why use threading.Timer just fire only one times
        refreshRegisterThread = threading.Thread(target=self.refreshRegister)
        refreshRegisterThread.setDaemon(True)
        refreshRegisterThread.start()
        checkServiceProviderThread = threading.Thread(target=self.checkServiceProvider)
        checkServiceProviderThread.setDaemon(True)
        checkServiceProviderThread.start()

    def shutdown(self,s=None,e=None):
        ''' 还需要再写写
        '''
        self.stopEvent.set()
        self.logger.info("got shutdown signale , exit graceful")
        event = threading.Event()
        event.wait(5)
        self.zk.stop()
        event.wait(5)
        self.daemon.shutdown()

    def refreshRegister(self):
        self.logger.info("background register refresh thread start ")
        while not self.stopEvent.isSet():
            for name in self.registerDict.keys():
                if not self.zk.connected:
                    self.logger.warning("zk connection lost , skip this time")
                    continue
                nodePath = None
                try:
                    nodePath = self.getNodePath(name)
                except:
                    self.logger.error(traceback.format_exc())
                if nodePath and not self.zk.exists(nodePath):
                    try:
                        self.logger.warning("nodePath:%s not exists , try to register again", nodePath)
                        self.zk.create(nodePath, ephemeral=True, makepath=True)
                        self.zk.set(nodePath,self.registerDict[name])
                        self.logger.warning("nodePath:%s register success", nodePath)
                    except:
                        traceback.print_exc()
                else:
                    self.logger.debug("nodePath:%s exists ", nodePath)
                self.stopEvent.wait(5)

    def checkServiceProvider(self):
        ''' self.serviceCache[servicePath][childName]
        '''
        self.logger.info("background service cache refresh thread start")
        while self.stopEvent.isSet():
            if not self.zk.connected:
                self.logger.warning("zk connection lost , skip this time")
                continue
            for name in self.serviceCache.keys():
                providerPath = self.getProviderPath(name)
                childNames = self.zk.get_children(providerPath)
                self.logger.debug("childNames In ZK:%s , Keys in Cache:%s",
                                  str(childNames),
                                  str(self.serviceCache[name].keys()))
                for childName in set(self.serviceCache[name].keys()) - set(childNames):
                    del(self.serviceCache[name][childName])
                for childName in set(childNames) - set(self.serviceCache[name].keys()):
                    self._addServiceCacheItem(name, childName)
            self.stopEvent.wait(5)

    def zkConnectionReady(self):
        ''' May be not work
        '''
        self.logger.info("self.zk.connected:"+str(self.zk.connected))
        self.logger.info("self.zk.get_children('/'):" + str(self.zk.get_children("/")))
        return self.zk.connected and len(self.zk.get_children("/"))

    def getServicePath(self, name):
        return "/{root}/{service}".format(root=self.root, service=name)

    def getProviderPath(self, name):
        return self.getServicePath(name)+"/provider"

    def getNodePath(self,name):
        return "{servicePath}/provider/{node}".format(servicePath=self.getServicePath(name), node=self.zk.client_id[0])

    def register(self, name, obj):
        obj.zkPyro4_echo__ = lambda x: x
        uri = self.daemon.register(obj)
        nodePath = self.getNodePath(name)
        try:
            self.zk.create(nodePath, ephemeral=True, makepath=True)
            self.zk.set(nodePath, str(uri))
        except NodeExistsError:
            self.logger.warning(traceback.format_exc())
        finally:
            self.registerDict[name] = str(uri)
            #print self.registerDict
            self.logger.info("%s registered , name: %s , uri: %s ", obj, name, uri)

    def zkConnectionListener(self,state):
        self.logger.info("ZK connection status changed to : " + state)

    def requestLoop(self):
        self.logger.info("Pyro4 service start !")
        self.daemon.requestLoop()

    def _addServiceCacheItem(self,name,nodeName):
        # servicePath = self.getServicePath(name)
        providerPath = self.getProviderPath(name)
        uri = self.zk.get("{providerPath}/{node}".format(providerPath=providerPath, node=nodeName))[0]
        if name not in self.serviceCache:
            self.serviceCache[name] = {}
        self.serviceCache[name][nodeName] = uri
        self.logger.info("service cache add [%s][%s] = %s", name, nodeName, uri)

    def lookup(self, name):
        servicePath = self.getServicePath(name)
        nodePath = "{servicePath}/consumer/{node}".format(servicePath=servicePath, node=self.zk.client_id[0])
        providerPath = self.getProviderPath(name)
        try:
            if name in self.serviceCache:
                childNames = self.serviceCache[name].keys()
            else:
                try:
                    self.zk.create(nodePath, ephemeral=True, makepath=True)
                    childNames = self.zk.get_children(providerPath, include_data=False)
                    for childName in childNames:
                        self._addServiceCacheItem(name, childName)
                except Exception,ex:
                    self.logger.error( "get provider from ZK failed , return []")
                    self.logger.error( traceback.format_exc() )
                    childNames = []

            if len(childNames) == 0:
                ex = NoMoreServiceProviderException(name)
                self.logger.error(ex.message)
                raise ex

            if servicePath not in self.watchedServices:
                self.logger.info("servicePath:%s add to cache", servicePath)
                self.watchedServices.add(servicePath)
                self.logger.debug("add watcher to servicePath:%s", servicePath)
                @self.zk.ChildrenWatch(self.getProviderPath(name))
                def onProviderChanged(childNames):
                    # Maintain the service cache
                    self.logger.info("service providers changed : "+str(childNames))
                    for childName in set(self.serviceCache[name].keys()) - set(childNames):
                        del(self.serviceCache[name][childName])
                    for childName in set(childNames) - set(self.serviceCache[name].keys()):
                        self._addServiceCacheItem(name, childName)

            childName = self._selectNode(self.serviceCache[name].keys())
            uri = self.serviceCache[name][childName]
            # todo:这里需要更改为对象池缓冲，使lookup拥有更高的性能
            # todo:这里需要有一种机制判断异常，然后淘汰节点
            self.logger.info("lookup return Pyro4 uri : %s", uri)
            return Pyro4.Proxy(uri)
        except NodeExistsError:
            self.logger.error(traceback.format_exc())

    def _selectNode(self, nodes):
        self.logger.debug("_selectNode input : "+str(nodes))
        if len(nodes) == 1:
            return nodes[0]
        if True:
            self._selectNodeCounter += 1
            return nodes[self._selectNodeCounter % len(nodes)]
        random.shuffle(nodes)
        self.logger.debug("_selectNode output : "+str(nodes[0]))
        return nodes[0]


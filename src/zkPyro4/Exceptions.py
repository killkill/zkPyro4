#!/bin/env python
# -*- coding: UTF-8 -*-


class NoMoreServiceProviderException(Exception):
    '''
    when there is no service provider , raise this exception
    '''
    def __init__(self,serviceName):
        self.message = "No more service(%s) provider"%serviceName
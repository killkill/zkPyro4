#!/bin/env python
# -*- coding: UTF-8 -*-


def locateNS(*args, **kwargs):
    return locateZK(*args, **kwargs)


def locateZK(*args, **kwargs):
    from zkPyroClient import zkPyroClient
    return zkPyroClient(*args, **kwargs)
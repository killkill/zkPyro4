#!/bin/env python
# -*- coding: UTF-8 -*-

import logging
import sys
#logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("abc")
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler() #(stream=sys.stdout)
ch.setLevel(0)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


logger.debug('debug message')
logger.info('info message')
logger.warn('warn message')
logger.error('error message')
logger.critical('critical message')


#!/bin/python

import logging

class OurLogger:
    logger = logging
    logging.basicConfig(level=logging.DEBUG)
    def __init__(self):
        pass

logger = OurLogger.logger

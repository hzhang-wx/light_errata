#!/bin/python

import logging

class GenLogger:
	logging.basicConfig(level = logging.INFO,
			format   = '%(asctime)s %(filename)s %(levelname)s %(message)s',
			datefmt  = '%a, %d %b %Y %H:%M:%S')

	def __init__(self):
		pass

	def __getattr__(self, name):
		return getattr(logging, name)

genLogger = GenLogger()

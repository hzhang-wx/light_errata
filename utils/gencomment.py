#!/bin/python
from misc.logger    import *
from misc.configobj import ConfigObj
from utils.common   import *
import getopt
import sys


class genComment:
	def __init__(self):
		self.errataId     = ''
		self.__parseArgs()
		self.resultPath   = "./result"
		self.jobStatePath = '%s/%s.%s' %(self.resultPath, \
				self.errataId, 'jobstate')
		genLogger.info("jobStatePath      : %s", self.jobStatePath)
		self.jobState = ConfigObj(self.jobStatePath, encoding="utf8")
	
	@classmethod
	def usage(cls):
		print("Usage: %s -T genComment -e errataId [-h]" \
				%sys.argv[0])
		exit(1)

	def __parseArgs(self):
		opts,args = getopt.getopt(sys.argv[1:], "T:e:h")
		for opt, arg in opts:
			if opt == '-h':
				self.usage()
			elif opt == '-e':
				self.errataId = arg

		if not self.errataId:
			self.usage()

	def printComment(self):
		url = 'https://beaker.engineering.redhat.com/jobs/'
		for type in self.jobState:
			if type == 'Tps' or type == 'Srpm':
				print '%s test passed:' %type
				for jobid in self.jobState[type]:
					print "%s%s" %(url, jobid.split(':')[1])
				print
			else:
				print '%s test run, no regression detected:' %type
				for jobid in self.jobState[type]:
					print "%s%s" %(url, jobid.split(':')[1])
				print
	
	def start(self):
		self.printComment()

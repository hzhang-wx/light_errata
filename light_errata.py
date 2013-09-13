#!/bin/python
from misc.logger          import *
from misc.config          import *
from utils.jobsubmit	  import *
from utils.parsejob	      import *
import getopt
import sys

class MainControl:
	function    = ''
	supportFuns = ['submitJobs', 'parseJobs']

	def __init__(self):
		pass

	@classmethod
	def usage(cls):
		print "Usage: %s -T [ %s ] -h" %(sys.argv[0], \
				" ".join(cls.supportFuns))
		exit(1)


	@classmethod 	
	def parseArgs(cls):
		t_flag      = 0
		opts,args   = ('', '')

		try:
			opts,args = getopt.getopt(sys.argv[1:3], "T:h")
		except:
			pass

		for opt, arg in opts:
			if opt == '-h':
				cls.usage()
			if opt == '-T':
				t_flag = 1
				if not arg or arg not in cls.supportFuns:
					genLogger.error("Unsupported function")
					cls.usage()
					pass
				if arg == 'submitJobs':
					cls.function = JobSubmit()
				if arg == 'parseJobs':
					cls.function = ParseJob()

		if not t_flag:
			cls.usage()

	@classmethod
	def start(cls):
		cls.function.start()

MainControl.parseArgs()
MainControl.start()

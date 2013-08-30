#!/bin/python
from feedme.feedme_beaker import *
from misc.logger          import *
from misc.config          import *
from utils.jobsubmit	  import *
import getopt
import sys

class MainControl:
	function    = ''
	supportFuns = ['submitJobs']

	def __init__(self):
		pass

	@classmethod
	def usage(cls):
		print "Usage: %s -T [ %s ] -h" %(sys.argv[0], \
				" ".join(cls.supportFuns))
		exit(1)


	@classmethod 	
	def parseArgs(cls):
		opts,args = getopt.getopt(sys.argv[1:], "T:e:t:h")
		for opt, arg in opts:
			if opt == '-h':
				cls.usage()
			if opt == '-T':
				if not arg or arg not in cls.supportFuns:
					genLogger.error("Unsupported function")
					usage()
					pass
				if arg == 'submitJobs':
					cls.function = JobSubmit()

	@classmethod
	def start(cls):
		genLogger.info("Now going to submit jobs...")
		cls.function.start()
		genLogger.info("Jobs all submited :)")

MainControl.parseArgs()
MainControl.start()

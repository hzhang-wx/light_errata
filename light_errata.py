#!/bin/python
from feedme.feedme_beaker import *
from misc.logger          import *
from misc.config          import *
from utils.jobsubmit	  import *
import getopt
import sys

#Global
task = ''
allTasks = 'submitJobs'
def usage():
	print "Usage: %s -T [ %s ] -h" %(sys.argv[0], allTasks)
	exit(1)

def parseArgs():
	global task, allTasks
	opts,args = getopt.getopt(sys.argv[1:], "T:e:t:h")
	for opt, arg in opts:
		if opt == '-h':
			usage()
		if opt == '-T':
			task = arg
			if arg == 'submitJobs':
				submParseArgs()

	if not task or task not in allTasks.split(' '):
		genLogger.error("Unsupported function")
		usage()


# For submit jobs
errataName   = ''
type2Tested  = ''
allTests     = 'tps srpm tier1 tier2 regression fj virt'

def submUsage():
	global allTests
	print "Usage: %s -T submitJobs -e errataId [-t "\
			"[%s] -h]" %(sys.argv[0], allTests)
	exit(1)

def submParseArgs():
	global errataName, type2Tested, allTests
	opts,args = getopt.getopt(sys.argv[1:], "T:e:t:h")
	for opt, arg in opts:
		if opt == '-h':
			submUsage()
		elif opt == '-e':
			errataName = arg
		elif opt ==  '-t':
			type2Tested = arg

	if not errataName:
		submUsage()

	if not type2Tested:
		type2Tested = allTests

	type2Tested = type2Tested.split(' ')
	for type in type2Tested:
		if type not in allTests.split(' '):
			submUsage()
	
parseArgs()



genLogger.info("Now going to submit jobs...")

job2sub = JobSubmit(errataName)

genLogger.info("type2Tested       :%s" %type2Tested)

for type in type2Tested:
	if type == 'tps':
		job2sub.jobType2Tested['tps'] = 'y'
	if type == 'srpm':
		job2sub.jobType2Tested['srpm'] = 'y'
	if type == 'tier1':
		job2sub.jobType2Tested['tier1'] = 'y'
	if type == 'tier2':
		job2sub.jobType2Tested['tier2'] = 'y'
	if type == 'regression':
		job2sub.jobType2Tested['regression'] = 'y'
	if type == 'fj':
		job2sub.jobType2Tested['fj'] = 'y'
	if type == 'virt':
		job2sub.jobType2Tested['virt'] = 'y'

job2sub.submAll()

#submit jobs end





#!/bin/python
from misc.logger      import *
from utils.common     import *
from feedme.jobresult import *
from misc.configobj   import ConfigObj
import getopt


class ParseJob:
	def __init__(self):
		self.autoRerun        = 'y'
		self.parseKnownIssues = 'y'
		self.errataName       = ''
		self.__parseArgs()
		self.errataInfo       = ErrataInfo(self.errataName)

		self.resultPath       = "./result"
		self.jobStatePath     = '%s/%s.%s' %(self.resultPath, \
				self.errataName, 'jobstate')
		genLogger.info("jobStatePath      : %s", self.jobStatePath)
		self.jobState = ConfigObj(self.jobStatePath, encoding="utf8")

		self.knownIssuesPath  = []
		self.knownIssues      = []
		self.knownIssuesRPath = "./known_issues"
		self.knownIssuesPath.append('%s/%s.%s' %(self.knownIssuesRPath, \
				self.errataInfo.rhel_version, "known_issues"))
		self.knownIssuesPath.append('%s/RHEL-%s.%s' %(self.knownIssuesRPath, \
				self.errataInfo.major, "known_issues"))
		for i in range(0, len(self.knownIssuesPath)):
			str = "%d  : %s" %(i, self.knownIssuesPath[i])
			genLogger.info("knownIssuesPath%s" %str)
			self.knownIssues.append(ConfigObj(self.knownIssuesPath[i], encoding="utf8"))

	@classmethod
	def usage(cls):
		print("Usage: %s -T parseJobs -e errataName [-r -h]" \
				%sys.argv[0])
		exit(1)

	def __parseArgs(self):
		opts,args = getopt.getopt(sys.argv[1:], "T:e:rh")
		for opt, arg in opts:
			if opt == '-h':
				self.usage()
			elif opt == '-r':
				self.autoRerun        = 'y'
				self.parseKnownIssues = 'n'
			elif opt == '-e':
				self.errataName = arg

		if not self.errataName:
			self.usage()

	def __fillConfig(self, job):
		pass

	def __parseKnownIssues(self, jobs):
		pass

	def __autoRerun(self, jobs):
		pass
			
	def start(self):
		for t in self.jobState:
			if not self.jobState[t]:
				genLogger.info("No %s jobs found, myabe you need to add manually" %t)
				continue
			genLogger.info("Start to parse %s jobs..." %t)
			jobs = []
			for jid in self.jobState[t]:
				reruned, parsed = ('n', 'n')
				for flag in self.jobState[t][jid]['status'].split("|"):
					if flag == 'Parsed':
						parsed = 'y'
						genLogger.info("Job %s has been Prased, SKIP" %jid)
					elif flag == 'Reruned':
						reruned = 'y'
						genLogger.info("Job %s has been Reruned, SKIP" %jid)
					else:
						genLogger.error("Unknow %s %s status flag: %s" %(t, jid, flag))
						exit(1)
				if parsed == 'y' and reruned == 'y':
					continue
				jobs.append(JobResult(jid))
				jobs[-1].type = t
				self.__fillConfig(jobs[-1])
			if self.parseKnownIssues == 'y' and parsed != 'y':
				genLogger.info("Start to parse %s jobs known issues..." %t)
				self.__parseKnownIssues(jobs)
				genLogger.info("%s jobs known issues parsed" %t)
			if self.autoRerun == 'y' and reruned != 'y':
				genLogger.info("Start to parse %s jobs needed to rerun..." %t)
				self.__autoRerun(jobs)
				genLogger.info("%s jobs reruned which need to be" %t)
				print jobs
			genLogger.info("End to parse %s jobs" %t)
		genLogger.info("All jobs parsed")

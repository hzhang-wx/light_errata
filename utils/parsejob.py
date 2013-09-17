#!/bin/python
from misc.logger      import *
from utils.common     import *
from feedme.jobresult import *
from misc.configobj   import ConfigObj
import getopt
import codecs


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

	def __addedRS2Rerun(self, id, jobxml):
		cloneJobXml("RS:%s" %id)
		xml = minidom.parse("%s/RS:%s.xml" %(TMP_DIR, id))
		if not jobxml:
			jobxml = xml
			return jobxml
		for n in xml.documentElement.childNodes:
			if n.nodeName == "recipeSet":
				jobxml.documentElement.appendChild(n)
		return jobxml

	def __autoRerun(self, jobs):
		jobxml = None 
		for job in jobs:
			if job.result['status'] != 'Completed':
				genLogger.warn("%s J:%s status %s, not Completed, SKIP" \
						%(job.type, job.result['id'], job.result['status']))
				continue
			for rs in job.result['recipeSet']:
				end_by_task       = False
				end_by_guest      = False
				end_by_guest_task = False
				for r in rs.result['recipe']:
					if end_by_task or end_by_guest or end_by_guest_task:
						break
					if r.result['status'] == 'Aborted' or r.result['status'] == 'Panic':
						genLogger.info('%s J:%s RS:%s adding to rerun since R:%s %s' \
								%(job.type, job.result['id'], rs.result['id'], r.result['id'], r.result['status']))
						jobxml = self.__addedRS2Rerun(rs.result['id'], jobxml)
						break
					for t in r.result['task']:
						if t.result['status'] == 'Aborted':
							genLogger.info('%s J:%s RS:%s adding to rerun since T:%s Aborted' \
								%(job.type, job.result['id'], rs.result['id'], t.result['id']))
							jobxml = self.__addedRS2Rerun(rs.result['id'], jobxml)
							end_by_task = True
							break
					for gr in rs.result['guestrecipe']:
						if end_by_guest_task:
							break
						if gr.result['status'] == 'Aborted' or gr.result['status'] == 'Panic':
							genLogger.info('%s J:%s RS:%s adding to rerun since Guest R:%s %s' \
									%(job.type, job.result['id'], rs.result['id'], gr.result['id'], gr.result['status']))
							jobxml = self.__addedRS2Rerun(rs.result['id'], jobxml)
							end_by_guest = True
							break
						for gt in gr.result['task']:
							if gt.result['status'] == 'Aborted':
								genLogger.info('%s J:%s RS:%s adding to rerun since Guest T:%s Aborted' \
									%(job.type, job.result['id'], rs.result['id'], gt.result['id']))
								jobxml = self.__addedRS2Rerun(rs.result['id'], jobxml)
								end_by_guest_task = True
								break
	
		if not jobxml:
			genLogger.info("No %s jobs need to rerun" %jobs[0].type)
			return

		wb = jobxml.documentElement.getElementsByTagName\
				('whiteboard')[0].childNodes[0].nodeValue
		new_wb = "Rerun %s" %wb
		jobxml.documentElement.getElementsByTagName\
				('whiteboard')[0].childNodes[0].nodeValue = new_wb
		f = file("%s/%s.rerun" %(TMP_DIR, jobs[0].type), 'w')
		writer = codecs.lookup('utf-8')[3](f)
		jobxml.writexml(writer, encoding='utf-8')
		writer.close()

		cmd = 'bkr job-submit %s/%s.rerun' %(TMP_DIR, jobs[0].type)
		jobid = submBkr(cmd, jobs[0].type)

		self.jobState[jobs[0].type][jobid] = { 'wb': new_wb, 'status': ''}
		for job in jobs:
			if not self.jobState[job.type]['J:%s' %job.result['id']]['wb']:
				self.jobState[job.type]['J:%s' %job.result['id']]['wb'] = job.result['wb']
			if not self.jobState[job.type]['J:%s' %job.result['id']]['status']:
				self.jobState[job.type]['J:%s' %job.result['id']]['status'] = 'Reruned'
			else:
				self.jobState[job.type]['J:%s' %job.result['id']]['status'] += '|Reruned'
		self.jobState.write()
			
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
					elif flag:
						genLogger.error("Unknow %s %s status flag: %s" %(t, jid, flag))
						exit(1)
				if parsed == 'y' and reruned == 'y':
					continue
				jobs.append(JobResult(jid))
				jobs[-1].type = t
			if self.parseKnownIssues == 'y' and parsed != 'y':
				genLogger.info("Start to parse %s jobs known issues..." %t)
				self.__parseKnownIssues(jobs)
				genLogger.info("%s jobs known issues parsed end" %t)
			if self.autoRerun == 'y' and reruned != 'y':
				genLogger.info("Start to parse %s jobs needed to rerun..." %t)
				self.__autoRerun(jobs)
				genLogger.info("%s jobs reruned end" %t)
			genLogger.info("End to parse %s jobs" %t)
		genLogger.info("All jobs parsed")

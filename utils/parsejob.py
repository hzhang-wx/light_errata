#!/bin/python
from misc.logger      import *
from utils.common     import *
from feedme.jobresult import *
from misc.configobj   import ConfigObj
import getopt
import codecs


class ParseJob:
	def __init__(self):
		self.autoRerun        = ''
		self.parseKnownIssues = ''
		self.errataName       = ''
		self.__parseArgs()
		self.errataInfo       = ErrataInfo(self.errataName)

		self.resultPath       = "./result"
		self.jobStatePath     = '%s/%s.%s' %(self.resultPath, \
				self.errataName[0:-3], 'jobstate')
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
		print("Usage: %s -T parseJobs -e errataName [-r -p -h]" \
				%sys.argv[0])
		exit(1)

	def __parseArgs(self):
		opts,args = getopt.getopt(sys.argv[1:], "T:e:rph")
		for opt, arg in opts:
			if opt == '-h':
				self.usage()
			elif opt == '-r':
				self.autoRerun        = 'y'
			elif opt == '-p':
				self.parseKnownIssues = 'y'
			elif opt == '-e':
				self.errataName = arg

		if not self.errataName:
			self.usage()

		if not self.autoRerun and not self.parseKnownIssues:
			self.usage()

	def __parseTask(self, ctx):
		(job, rs, r, gr, t) = (ctx['job'], ctx['rs'], ctx['r'], ctx['gr'], ctx['t'])
		for result in t.result['results'].results:
			if result.result['result'] == 'Fail':
				print getLogPath(job.logsPath, result.result['id'], \
						self.knownIssues['%s' %result.result['path']]['logname'])
			if result.result['result'] == 'Panic':
				pass
				# As unknown issue
			if result.result['result'] == 'Warn' and t.result['status'] == 'Aborted':
				pass
				# ToDo parse

	def __parseKnownIssues(self, jobs):
		for job in jobs:
			if job.parsed:
				continue
			if job.result['status'] != 'Completed' and job.result['status'] != 'Aborted':
				genLogger.warn("%s J:%s status %s, not Completed or Aborted, SKIP" \
						%(job.type, job.result['id'], job.result['status']))
				continue
			if job.result['result'] == 'Pass':
				genLogger.debug("%s J:%s result %s, SKIP" \
						%(job.type, job.result['id'], job.result['result']))
				continue
			for rs in job.result['recipeSet']:
				skip_left = ''
				for r in rs.result['recipe']:
					if r.result['result'] == 'Pass':
						continue
					if skip_left:
						skip_left = ''
						continue
					for t in r.result['task']:
						if t.result['result'] == 'Pass':
							continue
						ctx = { 'job': job, 'rs': rs, 'r': r, 'gr': '', 't': t } 
						ret = self.__parseTask(ctx)
						if ret == 'SKIP_LEFT':
							skip_left = True
							break
					skip_left_gr = ''
					for gr in r.result['guestrecipe']:
						if gr.result['result'] == 'Pass':
							continue
						if skip_left_gr:
							skip_left_gr = ''
							continue
						for gt in gr.result['task']:
							if gt.result['result'] == 'Pass':
								continue
							ctx = { 'job': job, 'rs': rs, 'r': r, 'gr': gr, 't': t } 
							ret = self.__parseTask(ctx)
							if ret == 'SKIP_LEFT':
								skip_left_gr = True
								break

		self.__updateJobState(jobs, 'Parsed')
		self.jobState.write()
			
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

	def __updateJobState(self, jobs, flag):
		for job in jobs:
			if not self.jobState[job.type]['J:%s' %job.result['id']]['wb']:
				self.jobState[job.type]['J:%s' %job.result['id']]['wb'] = job.result['wb']
			if (flag == 'Reruned' and job.reruned) or (flag == 'Parsed' and job.parsed):
				continue
			if not self.jobState[job.type]['J:%s' %job.result['id']]['status']:
				self.jobState[job.type]['J:%s' %job.result['id']]['status'] = flag
			else:
				self.jobState[job.type]['J:%s' %job.result['id']]['status'] += '|%s' %flag

	def __autoRerun(self, jobs):
		jobxml = None 
		for job in jobs:
			if job.reruned:
				continue
			if job.result['status'] != 'Completed' and job.result['status'] != 'Aborted':
				genLogger.warn("%s J:%s status %s, not Completed or Aborted, SKIP" \
						%(job.type, job.result['id'], job.result['status']))
				continue
			if job.result['result'] == 'Pass':
				genLogger.debug("%s J:%s result %s, SKIP" \
						%(job.type, job.result['id'], job.result['result']))
				continue
			for rs in job.result['recipeSet']:
				end_by_task       = False
				end_by_guest      = False
				end_by_guest_task = False
				for r in rs.result['recipe']:
					if end_by_task or end_by_guest or end_by_guest_task:
						break
					if r.result['result'] == 'Pass':
						continue
					if r.result['status'] == 'Aborted' or r.result['result'] == 'Panic' or \
							r.result['result'] == 'Cancelled':
						genLogger.info('%s J:%s RS:%s adding to rerun since R:%s %s' \
								%(job.type, job.result['id'], rs.result['id'], r.result['id'], r.result['status']))
						jobxml = self.__addedRS2Rerun(rs.result['id'], jobxml)
						break
					for t in r.result['task']:
						if t.result['status'] == 'Aborted' or t.result['status'] == 'Cancelled':
							genLogger.info('%s J:%s RS:%s adding to rerun since T:%s Aborted' \
								%(job.type, job.result['id'], rs.result['id'], t.result['id']))
							jobxml = self.__addedRS2Rerun(rs.result['id'], jobxml)
							end_by_task = True
							break
					for gr in r.result['guestrecipe']:
						if end_by_guest_task:
							break
						if gr.result['result'] == 'Pass':
							continue
						if gr.result['status'] == 'Aborted' or gr.result['result'] == 'Panic' or \
								gr.result['status'] == 'Cancelled':
							genLogger.info('%s J:%s RS:%s adding to rerun since Guest R:%s %s' \
									%(job.type, job.result['id'], rs.result['id'], gr.result['id'], gr.result['status']))
							jobxml = self.__addedRS2Rerun(rs.result['id'], jobxml)
							end_by_guest = True
							break
						for gt in gr.result['task']:
							if gt.result['status'] == 'Aborted' or gt.result['status'] == 'Cancelled':
								genLogger.info('%s J:%s RS:%s adding to rerun since Guest T:%s Aborted' \
									%(job.type, job.result['id'], rs.result['id'], gt.result['id']))
								jobxml = self.__addedRS2Rerun(rs.result['id'], jobxml)
								end_by_guest_task = True
								break

		if not jobxml:
			self.__updateJobState(jobs, 'Reruned')
			self.jobState.write()
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

		self.__updateJobState(jobs, 'Reruned')

		self.jobState[jobs[0].type][jobid] = { 'wb': new_wb, 'status': ''}
		self.jobState.write()
			
	def start(self):
		for t in self.jobState:
			if not self.jobState[t]:
				genLogger.info("No %s jobs found, myabe you need to add manually" %t)
				continue
			genLogger.info("Start to parse %s jobs..." %t)
			jobs = []
			for jid in self.jobState[t]:
				reruned, parsed = ('', '')
				for flag in self.jobState[t][jid]['status'].split("|"):
					if flag == 'Parsed' and self.parseKnownIssues == 'y':
						parsed = 'y'
						genLogger.info("Job %s has been Prased, SKIP" %jid)
					if flag == 'Reruned' and self.autoRerun == 'y':
						reruned = 'y'
						genLogger.info("Job %s has been Reruned, SKIP" %jid)
					if flag != 'Reruned' and flag != 'Parsed':
						genLogger.error("Unknow %s %s status flag: %s" %(t, jid, flag))
						exit(1)
				if (parsed == 'y' or not self.parseKnownIssues) and \
						(reruned == 'y' or not self.autoRerun):
					continue
				jobs.append(JobResult(jid))
				jobs[-1].type    = t
				jobs[-1].parsed  = parsed
				jobs[-1].reruned = reruned
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

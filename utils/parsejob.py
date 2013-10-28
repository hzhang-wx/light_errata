#!/bin/python
from misc.logger      import *
from utils.common     import *
from feedme.jobresult import *
from misc.configobj   import ConfigObj
import getopt
import codecs
import os
import asciitable


class ParseJob:
	def __init__(self):
		self.autoRerun        = ''
		self.parseKnownIssues = ''
		self.errataName       = ''
		self.errataLname      = ''
		self.rerunedRSId      = []
		self.force            = False
		self.__parseArgs()
		self.errataInfo       = ErrataInfo(self.errataName, self.errataLname, False)

		self.resultPath       = "./result"
		self.jobStatePath     = '%s/%s.%s' %(self.resultPath, \
				self.errataInfo.errataId, 'jobstate')
		genLogger.info("jobStatePath      : %s", self.jobStatePath)
		self.jobState = ConfigObj(self.jobStatePath, encoding="utf8")

		if self.parseKnownIssues == 'y':
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
	
			self.knownIssuesResult   = '%s/%s.%s' %(self.resultPath, \
					self.errataInfo.errataId, 'knownIssues')
			self.unknownIssuesResult = '%s/%s.%s' %(self.resultPath, \
					self.errataInfo.errataId, 'unknownIssues')
			self.tableTemple = {'Path': ['---'], 'TaskName': ['---'], 'TaskResult': ['---'],\
					'TaskStatus': ['---'], 'ResultPath': ['---'], 'PathResult': ['---'], \
					'Checked': ['---']}
			self.columns = ['Path', 'TaskName', 'TaskResult', 'TaskStatus', \
					'ResultPath', 'PathResult', 'Checked']
			if not os.path.exists(self.knownIssuesResult):
				asciitable.write(self.tableTemple, self.knownIssuesResult, \
						names = self.columns, Writer=asciitable.FixedWidth)
			if not os.path.exists(self.unknownIssuesResult):
				asciitable.write(self.tableTemple, self.unknownIssuesResult, \
						names = self.columns, Writer=asciitable.FixedWidth)
			reader = asciitable.get_reader(Reader=asciitable.FixedWidth)
			self.knownIssuesTable   = reader.read(self.knownIssuesResult)
			self.unknownIssuesTable = reader.read(self.unknownIssuesResult)

	@classmethod
	def usage(cls):
		print("Usage: %s -T parseJobs -e errataName [-l lastErrataName] [-r -p -f -h]" \
				%sys.argv[0])
		exit(1)

	def __parseArgs(self):
		opts,args = getopt.getopt(sys.argv[1:], "T:e:l:rpfh")
		for opt, arg in opts:
			if opt == '-h':
				self.usage()
			elif opt == '-r':
				self.autoRerun        = 'y'
			elif opt == '-p':
				self.parseKnownIssues = 'y'
			elif opt == '-f':
				self.force = True
			elif opt == '-e':
				self.errataName = arg
			elif opt == '-l':
				self.errataLname = arg

		if not self.errataName:
			self.usage()

		if not self.autoRerun and not self.parseKnownIssues:
			self.usage()

	def __isKnownIssue(self, task, path):
		for known_issue in self.knownIssues:
			if known_issue.has_key(task):
				if known_issue[task].has_key(path):
					return known_issue[task][path]
		return False

	def __add2Table(self, ctx, result, known_issues):
		(job, rs, r, gr, t) = (ctx['job'], ctx['rs'], ctx['r'], ctx['gr'], ctx['t'])
		if gr:
			path = '%s/J:%s/RS:%s/R:%s/GR:%s/T:%s' %(job.type, \
					job.result['id'], rs.result['id'], r.result['id'], \
							gr.result['id'], t.result['id'])
		else:
			path = '%s/J:%s/RS:%s/R:%s/T:%s' %(job.type, \
					job.result['id'], rs.result['id'], r.result['id'], \
							t.result['id'])
		task_name   = t.result['name']
		task_result = t.result['result']
		task_status = t.result['status']
		result_path = result.result['path']
		path_result = result.result['result']


		if known_issues == 'yes':
			index = len(self.knownIssuesTable['Path'])
			start = False
			for i, v in enumerate(self.knownIssuesTable['Path']):
				if v.split('/')[0] == job.type: 
					start = True
					if start and v.split('/')[0] != job.type:
						index = i
						break
			checked     = '*'
			self.knownIssuesTable['Path'].insert(index, path.encode('ascii', 'replace'))
			self.knownIssuesTable['TaskName'].insert(index, task_name.encode('ascii', 'replace'))
			self.knownIssuesTable['TaskResult'].insert(index, task_result.encode('ascii', 'replace'))
			self.knownIssuesTable['TaskStatus'].insert(index, task_status.encode('ascii', 'replace'))
			self.knownIssuesTable['ResultPath'].insert(index, result_path.encode('ascii', 'replace'))
			self.knownIssuesTable['PathResult'].insert(index, path_result.encode('ascii', 'replace'))
			self.knownIssuesTable['Checked'].insert(index, checked.encode('ascii', 'replace'))
		else:
			index = len(self.unknownIssuesTable['Path'])
			start = False
			for i, v in enumerate(self.unknownIssuesTable['Path']):
				if v.split('/')[0] == job.type: 
					start = True
					if start and v.split('/')[0] != job.type:
						index = i
						break
			checked     = 'No'
			self.unknownIssuesTable['Path'].insert(index, path.encode('ascii', 'replace'))
			self.unknownIssuesTable['TaskName'].insert(index, task_name.encode('ascii', 'replace'))
			self.unknownIssuesTable['TaskResult'].insert(index, task_result.encode('ascii', 'replace'))
			self.unknownIssuesTable['TaskStatus'].insert(index, task_status.encode('ascii', 'replace'))
			self.unknownIssuesTable['ResultPath'].insert(index, result_path.encode('ascii', 'replace'))
			self.unknownIssuesTable['PathResult'].insert(index, path_result.encode('ascii', 'replace'))
			self.unknownIssuesTable['Checked'].insert(index, checked.encode('ascii', 'replace'))

	def __parseTask(self, ctx):
		(job, rs, r, gr, t) = (ctx['job'], ctx['rs'], ctx['r'], ctx['gr'], ctx['t'])
		if not t.result['results']:
			return
		for result in t.result['results'].results:
			task = t.result['name']
			path = result.result['path']
			if result.result['result'] == 'Fail':
				issues =  self.__isKnownIssue(task, path)
				if issues:
					self.__add2Table(ctx, result, 'yes')
				else:
					self.__add2Table(ctx, result, 'no')
			if result.result['result'] == 'Panic':
					self.__add2Table(ctx, result, 'no')
					return 'SKIP_LEFT'
			if result.result['result'] == 'Warn' and t.result['status'] == 'Aborted':
					if t.result['name'] == '/distribution/install':
						self.__add2Table(ctx, result, 'yes')
						return 'SKIP_LEFT'
					elif result.result['path'] == '/':
						self.__add2Table(ctx, result, 'no')
						return 'SKIP_LEFT'
					else:
						self.__add2Table(ctx, result, 'no')

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
				if rs.result['response'] == 'nak':
					continue
				skip_left = ''
				for r in rs.result['recipe']:
					if r.result['result'] == 'Pass' and not r.result['guestrecipe']:
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
							ctx = { 'job': job, 'rs': rs, 'r': r, 'gr': gr, 't': gt } 
							ret = self.__parseTask(ctx)
							if ret == 'SKIP_LEFT':
								skip_left_gr = True
								break

		self.__updateJobState(jobs, 'Parsed')
		self.jobState.write()

		asciitable.write(self.knownIssuesTable, self.knownIssuesResult, \
				names = self.columns, Writer=asciitable.FixedWidth)
		asciitable.write(self.unknownIssuesTable, self.unknownIssuesResult, \
				names = self.columns, Writer=asciitable.FixedWidth)

	def __addedRS2Rerun(self, id, jobxml):
		self.rerunedRSId.append(id)
		cloneJobXml("RS:%s" %id)
		xml = minidom.parse("%s/RS:%s.xml" %(TMP_DIR, id))
		if not jobxml:
			jobxml = xml
			return jobxml
		for n in xml.documentElement.childNodes:
			if n.nodeName == "recipeSet":
				jobxml.documentElement.appendChild(n)
		return jobxml

	def __setResponse(self, value):
		for rsid in self.rerunedRSId:
			setResponse(rsid, value)
		self.rerunedRSId = []

	def __updateJobState(self, jobs, flag):
		for job in jobs:
			if job.result['status'] != 'Completed' and job.result['status'] != 'Aborted':
				continue
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
			if job.result['status'] != 'Completed' and \
				job.result['status'] != 'Aborted' and not self.force:
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
				if rs.result['response'] == 'nak':
					continue
				for r in rs.result['recipe']:
					if end_by_task or end_by_guest or end_by_guest_task:
						break
					if r.result['result'] == 'Pass':
						continue
					if r.result['status'] == 'Aborted' or r.result['result'] == 'Panic' or \
							r.result['status'] == 'Cancelled':
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

		self.__setResponse('nak')
			
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
					if flag != 'Reruned' and flag != 'Parsed' and flag:
						genLogger.error("Unknow %s %s status flag: %s" %(t, jid, flag))
						exit(1)
				if (parsed == 'y' or not self.parseKnownIssues) and \
						(reruned == 'y' or not self.autoRerun):
					continue
				jobs.append(JobResult(jid))
				jobs[-1].type    = t
				jobs[-1].parsed  = parsed
				jobs[-1].reruned = reruned
			if not jobs:
				continue
			if self.parseKnownIssues == 'y':
				genLogger.info("Start to parse %s jobs known issues..." %t)
				self.__parseKnownIssues(jobs)
				genLogger.info("%s jobs known issues parsed end" %t)
			if self.autoRerun == 'y':
				genLogger.info("Start to parse %s jobs needed to rerun..." %t)
				self.__autoRerun(jobs)
				genLogger.info("%s jobs reruned end" %t)
				genLogger.info("Please check reruned jobs in beaker")
			genLogger.info("End to parse %s jobs" %t)
		genLogger.info("All jobs parsed")
		if self.parseKnownIssues == 'y':
			genLogger.info("Please check the parsed results in below files:")
			genLogger.info("unKnown Issues: %s" %self.unknownIssuesResult)
			genLogger.info("Known   Issues: %s" %self.knownIssuesResult)

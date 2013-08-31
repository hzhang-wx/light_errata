#!/bin/python
from xml.dom import minidom
import os
import sys

class Job:
	''' Feed Beaker Job:
	Job = { 'id'		 : ''
			'name'	   : ''
			'type'	   : ''
			'whiteboard' : ''
			'result'	 : ''
			'status'	 : ''
			'recipeSet'  : [{ 'id'	 : '' 
							 'recipe' : [{ 'id'   : ''
										  'task' : [{ 'id'	  : ''
													 'name'	: ''
													 'result'  : ''
													 'status'  : ''
													 'results' : [{ 'id'	 = ''
																   'path'   = ''
																   'result' = ''
																 }]
													}]
										}]
							}]
		}
	'''
	def __init__(self, id, type, logger, config):
		self.logger = logger
		self.config = config
		self.jobBox = {'id' : id, 'type' : type}
		self.jobBox['recipeSet'] = []
		self.__grapXml(id)

	def __grapXml(self, id):
		cmd = 'bkr job-results --prettyxml J:%s > %s/job_%s.xml 2> %s/err.tmp' \
				%(id, self.config.tmpDir, id, self.config.tmpDir)
		self.logger.info("Grap Xml For Job: %s" %id)
		self.logger.debug("Cmd: %s" %cmd)
		ret = os.system(cmd)
		if (ret):
			f = open('%s/err.tmp' %self.config.tmpDir)
			self.logger.fatal(f.read())
			f.close()
			self.logger.shutdown()
			sys.exit(1);

	def feedJob(self):
		xml = minidom.parse("%s/job_%s.xml" %(self.config.tmpDir, self.jobBox['id']))
		job = xml.documentElement
		self.jobBox['id']		 = job.getAttributeNode('id').value
		self.jobBox['result']	 = job.getAttributeNode('result').value
		self.jobBox['status']	 = job.getAttributeNode('status').value
		self.jobBox['whiteboard'] = job.getElementsByTagName('whiteboard')[0].childNodes[0].nodeValue
		for node in job.childNodes:
			 if node.nodeName == "recipeSet":
				 rss  =  node
				 id = rss.getAttributeNode('id').value
				 self.jobBox['recipeSet'].append({'id' : id})
				 recipes = self.jobBox['recipeSet'][-1]['recipe'] = []
				 for rs in rss.getElementsByTagName('recipe'):
					id = rs.getAttributeNode('id').value
					recipes.append({'id' : id})
					tasks = recipes[-1]['task'] = []
					for task in rs.getElementsByTagName('task'):
						id	 = task.getAttributeNode('id').value
						result = task.getAttributeNode('result').value
						status = task.getAttributeNode('status').value
						tasks.append({'id' : id})
						tasks[-1]['result'] = result
						tasks[-1]['status'] = status
						results = tasks[-1]['results'] = []
						xml_results = task.getElementsByTagName('results')[0]
						for result in xml_results.getElementsByTagName('result'):
							id	 = result.getAttributeNode('id').value
							path   = result.getAttributeNode('path').value
							result = result.getAttributeNode('result').value
							results.append({'id' : id})
							results[-1]['path']   = path
							results[-1]['result'] = result


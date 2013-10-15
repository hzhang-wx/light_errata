#!/bin/python
from xml.dom      import minidom
from utils.common import *
from misc.logger  import *
import os
import sys

class Result:
	def __init__(self, node):
		self.result = { 'id'    : '',
						'path'  : '',
						'result': ''
	   }
		self.__feedMe(node)

	def __feedMe(self, node):
		self.result['id']     = node.getAttributeNode('id').value
		self.result['path']   = node.getAttributeNode('path').value
		self.result['result'] = node.getAttributeNode('result').value

class Results:
	def __init__(self, node):
		self.results = []
		self.__feedMe(node)

	def __feedMe(self, node):
		for n in node.childNodes:
			if n.nodeName == "result":
				self.results.append(Result(n))

class TaskResult:
	def __init__(self, node):
		self.result = { 'id'     : '',
						'name'   : '',
						'status' : '',
						'result' : '',
						'results': '',
	   }
		self.__feedMe(node)

	def __feedMe(self, node):
		self.result['id']     = node.getAttributeNode('id').value
		self.result['name']   = node.getAttributeNode('name').value
		self.result['status'] = node.getAttributeNode('status').value
		self.result['result'] = node.getAttributeNode('result').value
		for n in node.childNodes:
			if n.nodeName == "results":
				self.result['results'] = Results(n)

class GuestRecipeResult:
	def __init__(self, node):
		self.result = { 'id'         : '',
						'status'     : '',
						'result'     : '',
						'distro'     : '',
						'wb'         : '',
						'task'       : [],
	   }
		self.__feedMe(node)

	def __feedMe(self, node):
		self.result['id']     = node.getAttributeNode('id').value
		self.result['status'] = node.getAttributeNode('status').value
		self.result['result'] = node.getAttributeNode('result').value
		self.result['distro'] = node.getAttributeNode('distro').value
		self.result['wb']     = node.getAttributeNode('whiteboard').value
		for n in node.childNodes:
			if n.nodeName == "task":
				self.result['task'].append(TaskResult(n))

class RecipeResult:
	def __init__(self, node):
		self.result = { 'id'         : '',
						'status'     : '',
						'result'     : '',
						'system'     : '',
						'distro'     : '',
						'wb'         : '',
						'task'       : [],
						'guestrecipe': []
	   }
		self.__feedMe(node)

	def __feedMe(self, node):
		self.result['id']     = node.getAttributeNode('id').value
		self.result['status'] = node.getAttributeNode('status').value
		self.result['result'] = node.getAttributeNode('result').value
		if node.getAttributeNode('system'):
			self.result['system'] = node.getAttributeNode('system').value
		else:
			self.result['system'] = ''
		self.result['distro'] = node.getAttributeNode('distro').value
		self.result['wb']     = node.getAttributeNode('whiteboard').value
		for n in node.childNodes:
			if n.nodeName == "task":
				self.result['task'].append(TaskResult(n))
			if n.nodeName == "guestrecipe":
				self.result['guestrecipe'].append(GuestRecipeResult(n))

class RSResult:
	def __init__(self, node):
		self.result = { 'id'    : '',
				        'recipe': []
	   }
		self.__feedMe(node)

	def __feedMe(self, node):
		self.result['id'] = node.getAttributeNode('id').value
		for n in node.childNodes:
			if n.nodeName == "recipe":
				self.result['recipe'].append(RecipeResult(n))
		

class JobResult:
	def __init__(self, id):
		self.result = { 'id'       : id,
				        'wb'       : '',
				        'result'   : '',
				        'status'   : '',
				        'recipeSet': []
		}
		self.type     = ''
		self.parsed   = ''
		self.reruned  = ''
		self.logsPath  = ''
		self.__feedMe(id)

	def __feedMe(self, id):
		grabJobResult(id)
		xml = minidom.parse("%s/%s.xml" %(TMP_DIR, id))
		genLogger.debug("Start to load Job: %s xml" %id)
		job = xml.documentElement
		self.result['id']		 = job.getAttributeNode('id').value
		self.result['result']	 = job.getAttributeNode('result').value
		self.result['status']	 = job.getAttributeNode('status').value
		self.result['wb']        = job.getElementsByTagName('whiteboard')[0].childNodes[0].nodeValue
		#self.logsPath = grabLogsPath('J:%s' %self.result['id'])
		for n in job.childNodes:
			if n.nodeName == "recipeSet":
				self.result['recipeSet'].append(RSResult(n))
		genLogger.debug("Job: %s xml loaded" %id)

#!/bin/python
from   misc.logger      import *
from   misc.configobj   import ConfigObj
import commands
import xmlrpclib
import re
import os 

TMP_DIR='./tmp'

def grabJobResult(id):
	cmd = 'bkr job-results --prettyxml %s > %s/%s.xml' %(id, TMP_DIR, id)
	genLogger.debug("Grabed %s result xml" %id)
	output = shellCmd(cmd)
	return output

def cloneJobXml(id):
	cmd = 'bkr job-clone --dryrun --prettyxml %s > %s/%s.xml' %(id, TMP_DIR, id)
	genLogger.debug("Cloned %s xml" %id)
	output = shellCmd(cmd)
	return output

def grabLogsPath(id):
	cmd = 'bkr job-logs %s' %id
	genLogger.debug("Grabing %s logs path" %id)
	output = shellCmd(cmd)
	return output

def getLogPath(logs, id, name):
	pattern = re.compile(r'.*%s/%s' %(id, name))
	m = pattern.search(logs)
	if m:
		path = m.group(0)
	else:
		path = ''
	return path

def setResponse(id, value):
	cmd = 'bkr job-modify --response=%s RS:%s' %(value, id)
	genLogger.info("Modify RS:%s %s" %(id, value))
	output = shellCmd(cmd)
	return output

def shellCmd(cmd):
	(ret, output) = commands.getstatusoutput(cmd)
	if ret:
		genLogger.error("========CMD ERR INFO=============")
		genLogger.error("======== %s =============" %cmd)
		genLogger.error(output)
		genLogger.error("=============================")
		exit(1)
	return output

shellCmd('if [ ! -d %s ]; then mkdir -p %s; fi' %(TMP_DIR, TMP_DIR))

def submBkr(cmd, type):
	genLogger.info(cmd)
	output = shellCmd(cmd)
	pattern = re.compile(r'Submitted:.*(J:\d+).*\]')
	m = pattern.search(output)
	jobid = m.group(1)		
	genLogger.info("%s submited, %s" %(type, jobid))
	return jobid

class ErrataInfo:

	xmlRpc = 'http://errata-xmlrpc.devel.redhat.com/errata/errata_service'
	rl2distro = {
		'RHEL-6.2.Z'  : 'RHEL-6.2',
		'RHEL-6.3.Z'  : 'RHEL-6.3',
		'RHEL-6.4.Z'  : 'RHEL-6.4',
		'RHEL-5.10.Z' : 'RHEL5-Server-U10',
		'RHEL-5.9.Z'  : 'RHEL5-Server-U9',
		'RHEL-5.6.Z'  : 'RHEL5-Server-U6'
	}

	
	def __init__(self, name, lname = '', findLast = True):

		self.errataName  = name
		self.errataLname = lname
		self.errataId    = ''
		self.lversion    = ''
		self.errataLname = ''
		self.errataLid   = ''
		self.cachePath   = './result/errinfo.cache'
		self.cache       = {}
		self.errataLists = {}

		if not self.__getInfoFromCache() or \
				not self.cache[self.errataName]['lversion'] and findLast:
			self.cache[self.errataName] = {}
			self.cache[self.errataName]['rhel_version'] = ''
			self.cache[self.errataName]['version']      = '' 
			self.cache[self.errataName]['errataId']     = ''
			self.cache[self.errataName]['lversion']     = ''
			self.cache[self.errataName]['errataLname']  = ''
			self.cache[self.errataName]['errataLid']    = ''
			try:
				self.errata = xmlrpclib.ServerProxy(ErrataInfo.xmlRpc)
				self.errata.ping()
			except:
				genLogger.error("Could not connect to Errata. QUIT!")
				exit(1)
			self.errataLists = self.errata.get_advisory_list(\
				{"qe_group": "Kernel QE",\
				"product": "RHEL"})
			self.errataLists.reverse()
			for errata in self.errataLists:
				if errata['advisory_name'] == self.errataName:
					find_cur_errata = 1
					self.errataName = errata['advisory_name']
					self.errataId   = errata['errata_id']
					self.cache[self.errataName]['errataId'] = self.errataId
	
			packages = self.errata.get_base_packages_rhts(self.errataName)
			genLogger.debug("errata packages    : %s" %packages)
	
			self.rhel_version = packages[0]['rhel_version']
			self.version = packages[0]['version']
			self.cache[self.errataName]['rhel_version'] = self.rhel_version 
			self.cache[self.errataName]['version']      = self.version 
			if findLast:
				self.__findLastErrata()
			self.cache.write()


		self.distro  = self.rl2distro[self.rhel_version]
		pattern = re.compile(r'RHEL-(\d+)\.(\d+)\.(.*)')
		m = pattern.match(self.rhel_version)
		self.major = int(m.group(1))
		self.minor = int(m.group(2))
		self.zflag = m.group(3)	
		if self.major == 6 and self.minor == 3:
			self.zflag = 'EUS'

		self.bkrcommon = 'bkr workflow-kernel --prettyxml '\
			    '--hostrequire="group!=storage-qe" '\
			    '--retention_tag="120days" '\
			    '--distro=%s ' %self.distro
		arch = ''
		if self.major == 5:
			arch = '--arch=i386 --arch=x86_64 --arch=ppc64 --arch=ia64 --arch=s390x'
		if arch:
			self.bkrfj = self.bkrcommon
			self.bkrcommon = "%s %s" %(self.bkrcommon, arch)

		genLogger.info("errataName          : %s" %self.errataName)
		genLogger.info("errataId            : %s" %self.errataId)
		genLogger.info("rhel_version        : %s" %self.rhel_version)	
		genLogger.info("kernel_version      : %s" %self.version)	
		genLogger.info("last_kernel_version : %s" %self.lversion)	
		genLogger.debug("kernel major       : %s" %self.major)	
		genLogger.debug("kernel minor       : %s" %self.minor)	
		genLogger.debug("zflag              : %s" %self.zflag)	
		genLogger.info("lastErrataName      : %s" %self.errataLname)
		genLogger.info("lastErrataId        : %s" %self.errataLid)
		genLogger.info("distro              : %s" %self.distro)	
		genLogger.debug("bkr common cmd     : %s" %self.bkrcommon)	
	
	def __getInfoFromCache(self):
		if not os.path.exists(self.cachePath):
			os.mknod(self.cachePath)
			self.cache = ConfigObj(self.cachePath)
			return False
		else:
			self.cache = ConfigObj(self.cachePath)

		if self.cache.has_key(self.errataName):
			self.rhel_version = self.cache[self.errataName]['rhel_version']
			self.version      = self.cache[self.errataName]['version']
			self.errataId     = self.cache[self.errataName]['errataId']
			self.lversion     = self.cache[self.errataName]['lversion']
			self.errataLname  = self.cache[self.errataName]['errataLname']
			self.errataLid    = self.cache[self.errataName]['errataLid']
			return True
		else:
			return False
	
	def __findLastErrata(self):
		find_cur_errata  = 0
		for errata in self.errataLists:
			if errata['advisory_name'] == self.errataName:
				find_cur_errata = 1
				self.errataName = errata['advisory_name']
				self.errataId   = errata['errata_id']
				self.cache[self.errataName]['errataId'] = self.errataId
				genLogger.debug("Find current errata: %s" %self.errataName)

			elif find_cur_errata:
				if self.errataLname:
					packages = self.errata.get_base_packages_rhts\
						   (self.errataLname)
				else:
					packages = self.errata.get_base_packages_rhts\
						   (errata['advisory_name'])
					if not packages or packages[0]['rhel_version'] != self.rhel_version:
						continue
				for pkg in packages[0]['packages']:
					if pkg == "kernel":
						self.lversion    = packages[0]['version']
						self.errataLname = errata['advisory_name']
						self.errataLid   = errata['errata_id']
						self.cache[self.errataName]['lversion']    = self.lversion
						self.cache[self.errataName]['errataLname'] = self.errataLname
						self.cache[self.errataName]['errataLid']   = self.errataLid
						genLogger.debug("Find last errata: %s" %self.errataLname)
						return

		genLogger.error("ErrataLists        : %s" %errataLists)
		genLogger.error("Can't find Last Errata, Quit!")
		return 

from misc.logger import *
import xmlrpclib
import re
import os
import commands

class ErrataInfo:
	xmlRpc = 'http://errata-xmlrpc.devel.redhat.com/errata/errata_service'

	rl2distro = {
		'RHEL-6.2.Z' : 'RHEL-6.2',
		'RHEL-6.3.Z' : 'RHEL-6.3',
		'RHEL-6.4.Z' : 'RHEL-6.4',
		'RHEL-5.9.Z' : 'RHEL5-Server-U9',
		'RHEL-5.6.Z' : 'RHEL5-Server-U6'
	}

	def __init__(self, name):
		try:
			self.errataName  = name
			errata = xmlrpclib.ServerProxy(ErrataInfo.xmlRpc)
			errata.ping()
		except:
			genLogger.error("Could not connect to Errata. QUIT!")
			exit(1)

		packages = errata.get_base_packages_rhts(self.errataName)
		genLogger.debug("errata packages     : %s" %packages)
		errataLists = errata.get_advisory_list(\
				{"release": packages[0]['rhel_version'],\
				"qe_group": "Kernel QE"})
		genLogger.debug("errata lists: %s" %errataLists)
		self.errataLname = errataLists[-2]['advisory_name']
		self.errataLid   = errataLists[-2]['errata_id']
		self.errataId    = errataLists[-1]['errata_id']
		genLogger.info("errataName           : %s" %self.errataName)
		genLogger.info("lastErrataName       : %s" %self.errataLname)
		genLogger.info("errataId             : %s" %self.errataId)
		genLogger.info("lastErrataId         : %s" %self.errataLid)

		self.rhel_version = packages[0]['rhel_version']
		self.version = packages[0]['version']
		self.distro  = self.rl2distro[self.rhel_version]
		pattern = re.compile(r'RHEL-(\d)\.(\d)\.(.*)')
		m = pattern.match(self.rhel_version)
		self.major = m.group(1)		
		self.minor = m.group(2)
		self.zflag = m.group(3)	
		if int(self.major) == 6 and int(self.minor) == 3:
			self.zflag = 'EUS'
		lpackages = errata.get_base_packages_rhts(self.errataLname)
		genLogger.debug("last errata packages: %s" %lpackages)
		self.lversion = lpackages[0]['version']

		self.bkrcommon = 'bkr workflow-kernel --prettyxml '\
			    '--hostrequire="group!=storage-qe" '\
			    '--retention_tag="120days" '\
			    '--distro=%s ' %self.distro
		arch = ''
		if self.major == 5 and self.minor == 3:
			arch = '--arch=i386 --arch=x86_64 --arch=ia64 '
		elif self.major == 5:
			arch = '--arch=i386 --arch=x86_64 --arch=ppc64 --arch=ia64 --arch=s390x'
		if arch:
			self.bkrcommon = "%s %s" %(self.bkrcommon, arch)

		genLogger.info("rhel_version         : %s" %self.rhel_version)	
		genLogger.info("kernel_version       : %s" %self.version)	
		genLogger.debug("kernel major        : %s" %self.major)	
		genLogger.debug("kernel minor        : %s" %self.minor)	
		genLogger.debug("zflag               : %s" %self.zflag)	
		genLogger.info("last_kernel_version  : %s" %self.lversion)	
		genLogger.info("distro               : %s" %self.distro)	
		genLogger.debug("bkr common cmd      : %s" %self.bkrcommon)	
class JobSubmit(ErrataInfo):
	def __init__(self, name):
		self.jobType2Tested = {
			'tps'        : 'n',
			'srpm'       : 'n',
			'tier1'      : 'n',
			'tier2'      : 'n',
			'regression' : 'n',
			'fj'	     : 'n',
			'virt'       : 'n',
		}
		ErrataInfo.__init__(self, name)

	def submTps(self):
		genLogger.info("Tps submiting...")
		task = '--task=/kernel/errata/kernel-tps '\
		       '--taskparam="REL=%sServer-%s.%s.%s" '\
			'--taskparam="TESTARGS=%s" '\
			%(self.major, self.major, self.minor, self.zflag, self.errataId)
		wboard = '--whiteboard="%s Kernel TPS Testing for Errata" ' %self.distro
		extra = '--lite --nvr=%s ' %self.lversion
		bkrcommand = "%s %s %s %s" %(self.bkrcommon, task, wboard, extra)
		self.__submbkr(bkrcommand, "Tps")

	def submSrpm(self):
		genLogger.info("Srpm submiting...")
		task = '--task=/kernel/errata/srpm-rebuild '\
		       '--taskparam="TESTARGS=%s" ' %self.version
		wboard = '--whiteboard="%s Kernel SRPM Testing for Errata" ' %self.distro
		extra = '--lite --nvr=%s ' %self.lversion
		bkrcommand = "%s %s %s %s" %(self.bkrcommon, task, wboard, extra)
		self.__submbkr(bkrcommand, "Srpm")

	def submTier1(self):
		genLogger.info("Tier1 submiting...")
		task = '--type=KernelTier1 '
		version = '--nvr=%s ' %self.version
		extra = '--kvm '
		bkrcommand = "%s %s %s %s" %(self.bkrcommon, task, version, extra)
		self.__submbkr(bkrcommand, "Tier1")

	def submTier2(self):
		genLogger.info("Tier2 submiting...")
		task = '--type=KernelTier2 '
		version = '--nvr=%s ' %self.version
		extra = '--kvm '
		bkrcommand = "%s %s %s %s" %(self.bkrcommon, task, version, extra)
		self.__submbkrShirk(bkrcommand, "Tier2")
		
	def submRegression(self):
		genLogger.info("Regression submiting...")
		task   = ''
		task_z = ''
		for i in range(0, int(self.minor) + 1):
			task   = '--task=/kernel/errata/%s.%d %s' %(self.major, i, task)
			task_z = '--task=/kernel/errata/%s.%d.z %s' %(self.major, i, task_z)
		wboard = '--whiteboard="%s Kernel Regression Testing for Errata  %s" ' %(self.distro, self.errataId)
		version = '--nvr=%s ' %self.version
		extra = '--kvm '
		bkrcommand = "%s %s %s %s %s %s" %(self.bkrcommon, task, task_z, version, wboard, extra)
		self.__submbkr(bkrcommand, "Regression")
	
	def submVirt(self):
		genLogger.info("Virt submiting...")
		# FIXME: Use external program, implement later internal.
		cmd = 'cd ./misc && ./virt.py -d %s.%s -k %s | bkr job-submit -' %(self.major, self.minor, self.version)
		self.__submbkr(cmd, "Virt")

	def submFJ(self):
		if int(self.major) != 5:
			genLogger.warn("Only For RHEL-5, skip Fujitsu test")
			return
		genLogger.info("Fujitsu submiting...")

		task = '--task=/kernel/misc/gdb-simple '\
		       '--task=/kernel/misc/module-load '\
		       '--task=/kernel/errata/%s.%s ' %(self.major, self.minor)
		task = '%s --task=/kernel/errata/%s.%s.z ' %(task, self.major, self.minor)

		wboard = '--whiteboard="Kernel Regression Testing for the Fujitsu Machine for Errata %s" ' %self.errataId
		version = '--nvr=%s ' %self.version
		extra = '--arch=ia64 --keyvalue="HOSTNAME=pq0-0.lab.bos.redhat.com"'
		bkrcommand = "%s %s %s %s %s" %(self.bkrcommon, task, version, wboard, extra)
		self.__submbkrShirk(bkrcommand, "Fujitsu")

	def submAll(self):
		if self.jobType2Tested['tps'] == 'y':
			self.submTps()
		if self.jobType2Tested['srpm'] == 'y':
			self.submSrpm()
		if self.jobType2Tested['tier1'] == 'y':
			self.submTier1()
		if self.jobType2Tested['tier2'] == 'y':
			self.submTier2()
		if self.jobType2Tested['regression'] == 'y':
			self.submRegression()
		if self.jobType2Tested['fj'] == 'y':
			self.submFJ()
		if self.jobType2Tested['virt'] == 'y':
			self.submVirt()

	def __submbkrShirk(self, cmd, type):
		file = "./%s_tmp.xml" %type
		cmd_dry = "%s --dryrun > %s" %(cmd, file)
		genLogger.info(cmd_dry)
		self.__shellCmd(cmd_dry)
		if type == 'Tier2':
			self.__Tier2Shirk(file)
		if type == 'Fujitsu':
			self.__FjShirk(file)
		cmd = "bkr job-submit %s" %file
		jobid = self.__submbkr(cmd, type)
		cmd = 'rm -f %s' %file
		genLogger.debug(cmd)
		self.__shellCmd(cmd)
		return jobid

	def __submbkr(self, cmd, type):
		genLogger.info(cmd)
		output = self.__shellCmd(cmd)
		pattern = re.compile(r'Submitted:.*(J:\d+).*\]')
		m = pattern.search(output)
		jobid = m.group(1)		
		genLogger.info("%s submited, %s" %(type, jobid))
		return jobid


	def __Tier2Shirk(self, file):
		''' 
		Use /kernel/errata/xfstests to instead of
		/kernel/filesystems/xfs/xfstests
		'''
		cmd = "sed -i 's/\/kernel\/filesystems\/xfs\/xfstests/\/kernel\/errata\/xfstests/g' %s" %file
		genLogger.debug(cmd)
		self.__shellCmd(cmd)

	def __FjShirk(self, file):
		'''
		remove the virt host test from xml
		'''
		cmd = ''' grep -n "xen DOM0" Fujitsu_tmp.xml | awk -F ":" '{print $1}' '''
		genLogger.debug(cmd)
		line1 = int(self.__shellCmd(cmd)) - 1
		cmd = "sed -n  '%d, ${/<\/recipeSet>/=}' %s" %(line1, file)
		genLogger.debug(cmd)
		line2 = int(self.__shellCmd(cmd))
		cmd = "sed -i '%d,%d d' %s" %(line1, line2, file)
		genLogger.debug(cmd)
		self.__shellCmd(cmd)
		
		
	def __shellCmd(self, cmd):
		(ret, output) = commands.getstatusoutput(cmd)
		if ret:
			genLooger.error("========CMD ERR INFO=============")
			genLooger.error("======== %s =============" %cmd)
			genLooger.error(output)
			genLogger.error("=============================")
			exit(1)
		return output

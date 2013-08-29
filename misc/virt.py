#!/bin/env python3

from jinja2 import Template, Environment, FileSystemLoader
import argparse
import yaml
import re

config_yaml = 'virt.yaml'

def parse_args():
	class DistroAction(argparse.Action):
		def __call__(self, parser, namespace, values, option_string=None):
			global dmajor, dminor
			dmajor, dminor = map(int, re.match('(?:RHEL)?-?(\d+)\.(\d+).*', values, flags=re.I).groups())

	class KernelAction(argparse.Action):
		def __call__(self, parser, namespace, values, option_string=None):
			global kver
			kver, = re.match('(?:kernel-)?(.+)', values).groups()

	class ErrataAction(argparse.Action):
		def __call__(self, parser, namespace, values, option_string=None):
			raise NotImplementedError

	parser = argparse.ArgumentParser(description='Generate eus virt jobxml.')
	parser.add_argument('-d', '--distro', action=DistroAction, required=True,
			    help='e.g. -e  rhel6.4 | RHEL-6.4 | 6.4')
	group = parser.add_mutually_exclusive_group(required=True)
	group.add_argument('-k', '--kernel', action=KernelAction,
			   help='e.g. -k kernel-2.6.32-358.6.1.el6 | 2.6.32-358.6.1.el6')
	group.add_argument('-e', '--errata', action=ErrataAction,
			   help='e.g. -e RHSA-2013:14688 NOT IMPLEMENT!!')

	return parser.parse_args()

if __name__ == "__main__":
	args = parse_args()

	with open(config_yaml) as file:
		hconfig, varchs = yaml.load_all(file)

	env = Environment(loader=FileSystemLoader('.'))

	template = env.get_template('virt-host.django.xml')

	hyper_entries = hconfig['RHEL-%d' % dmajor]

	xml = template.render(hyper_entries=hyper_entries, varchs=varchs,
                      dmajor=dmajor, dminor=dminor, kver=kver)

	print(xml)

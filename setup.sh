#!/bin/bash
# Run please if fist use

# For misc/virt.py
# If without python3, may install python-PyYAML and python-jinja2
sudo yum install -y python3
sudo yum install -y python-PyYAML python-jinja2

# Install asciitable for praseJobs
tar xf misc/asciitable-0.8.0.tar.gz
cd asciitable-0.8.0 && python setup.py install --user && cd ..
rm -rf asciitable-0.8.0

echo 'Done.'

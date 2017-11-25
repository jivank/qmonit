#!/usr/bin/env python

import os
import sys
import re

pidfile = ''
script_helper = ''
directory = '/opt/qmonit'
if not os.path.exists(directory):
        os.makedirs(directory)

def make_executable(path):
    mode = os.stat(path).st_mode
    mode |= (mode & 0o444) >> 2    # copy R bits to X
    os.chmod(path, mode)

def find_monit_dir():
    reg = re.compile(r'include (\/.+)\*')
    with open('/etc/monit/monitrc') as monitrc:
        for line in monitrc:
            results = reg.findall(line)
            if results:
                return results[0]


def build_script(path,executable,args):
    global pidfile, script_helper
    script_helper = os.path.join(directory,executable+'.sh')
    script = '''#!/bin/bash
{} {} &
echo $! > /var/run/{}.pid'''.format(os.path.join(path,executable),args,executable)
    pidfile = os.path.join('/var/run/',executable+'.pid')
    with open(script_helper, 'w') as f: f.write(script)
    make_executable(script_helper)


def build_monit(path,executable):
    global pidfile, monit_path 
    monit = '''check process {} with pidfile {}
start program = "{}"
stop program = "/bin/kill `{}`"'''.format(
            executable,
            pidfile,
            script_helper,
            pidfile)
    monitfile = os.path.join(monit_path,executable)
    with open(monitfile,'w') as f: f.write(monit)


if __name__ == '__main__':
    arguments = dict(zip(['file','exe','args'], sys.argv))
    if not arguments.get('exe'): sys.exit('usage: qmonit.py <executable> "arg1 arg2 arg3"')
    monit_path = find_monit_dir()
    app = os.path.abspath(arguments['exe'])
    args = arguments.get('args') or ''
    dir_, name = os.path.split(app)
    build_script(dir_,name,args)
    build_monit(dir_,name)
    print('Done')



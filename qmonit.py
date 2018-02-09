#!/usr/bin/env python3

import os
import sys
import re
import subprocess
import shutil

QMONIT_DIR = '/opt/qmonit'

try:
    if not os.path.exists(QMONIT_DIR):
        os.makedirs(QMONIT_DIR)
except OSError as os_error:
    sys.exit("Please use a privileged account")

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
        sys.exit("Unable to find monit config folder")


def build_script(service_name, app_path, args, helper_script):
    script = '''#!/bin/bash
{} {} &
echo $! > /opt/qmonit/{}/{}.pid'''.format(app_path, args, service_name, service_name)
    with open(helper_script, 'w') as f:
        f.write(script)
    make_executable(helper_script)


def build_monit(monit_path, service_name, helper_script,pidfile):
    monit = '''check process {} with pidfile {}
start program = "{}" as uid {} and gid {}
stop program = "/bin/kill `{}`" as uid {} and gid {} '''.format(
    service_name,
    pidfile,
    helper_script,
    service_name,
    service_name,
    pidfile,
    service_name,
    service_name)

    monitfile = os.path.join(monit_path, service_name)
    with open(monitfile, 'w') as f:
        f.write(monit)


def create_user(service_name):
    subprocess.check_output("useradd -r --shell /bin/false {}".format(service_name).split())

def chown_folder(service_name, qmonit_service_dir):
    command = "chown -R {}:{} {}".format(service_name, service_name, qmonit_service_dir).split()
    subprocess.check_output(command)

def determine_app_path(executable):
    if os.path.isfile(executable):
        return os.path.abspath(executable)
    return shutil.which(executable) or exit('')


if __name__ == '__main__':
    ARGUMENTS = dict(zip(['file', 'service', 'exe', 'args'], sys.argv))
    if not ARGUMENTS.get('exe') or not ARGUMENTS.get('service'):
        sys.exit('usage: qmonit.py <service name> <executable> "arg1 arg2 arg3"')

    MONIT_PATH = find_monit_dir()
    SERVICE_NAME = ARGUMENTS.get('service')
    SERVICE_QM_DIR = os.path.join('/opt/qmonit', SERVICE_NAME)
    FULL_APP_PATH = determine_app_path(ARGUMENTS['exe'])
    ARGS = ARGUMENTS.get('args') or ''
    HELPER_SCRIPT = os.path.join(QMONIT_DIR, SERVICE_NAME, SERVICE_NAME + '.sh')
    PID_FILE = os.path.join('/opt/qmonit/', SERVICE_NAME, SERVICE_NAME+'.pid')

    os.makedirs(SERVICE_QM_DIR)

    build_script(SERVICE_NAME, FULL_APP_PATH, ARGS, HELPER_SCRIPT)
    build_monit(MONIT_PATH, SERVICE_NAME, HELPER_SCRIPT, PID_FILE)
    create_user(SERVICE_NAME)
    chown_folder(SERVICE_NAME, SERVICE_QM_DIR)

    print('Done')

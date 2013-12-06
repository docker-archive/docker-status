#!/usr/bin/env python
'''Deploy docker-status service monitoring docker registry and index

      ./deploy.py'''

from os import environ as env
import pexpect
from subprocess import call
import json
import re
import sys
import time

CONFIG = json.loads(env['CONFIG_JSON'])

# Populate environment variables
for key in CONFIG:
    env[key] = CONFIG[key]

app_id = "docker-status"    # Stashboard application id
docker_status_server = '{}.appspot.com'.format(app_id)
services = ['registry', 'index']
check_path = '{}/check.py'.format(env['APP_PATH'])


def retry(func, args=[], kwargs={}, sleep=0, count=5, hide_exc=False,
 func_success=lambda x: True):
    '''Return func(args) after count tries if not exception and func_success'''
    for i in range(count):
        if i:
            time.sleep(sleep)
        try:
            retval = func(*args, **kwargs)
            if func_success(retval):
                return retval
        except Exception, exc:
            pass
    if not hide_exc:
        raise exc


def setup_check():
    '''Load credentials on check.py for GAE upload'''
    # Oauth credentials need to be properly escaped
    env['OAUTH_KEY'] = re.sub('/', '\\/', env['OAUTH_KEY'])
    env['OAUTH_SECRET'] = re.sub('/', '\\/', env['OAUTH_SECRET'])
    call('sed -Ei "s/^(.*consumer_key = ).+/\\1\'{}\'/" {}'.format(
        env['CONSUMER_KEY'], check_path), shell=True)
    call('sed -Ei "s/^(.*consumer_secret = ).+/\\1\'{}\'/" {}'.format(
        env['CONSUMER_SECRET'], check_path), shell=True)
    call('sed -Ei "s/^(.*oauth_key = ).+/\\1\'{}\'/" {}'.format(
        env['OAUTH_KEY'], check_path), shell=True)
    call('sed -Ei "s/^(.*oauth_secret = ).+/\\1\'{}\'/" {}'.format(
        env['OAUTH_SECRET'], check_path), shell=True)


def gae_api(cmd, timeout=300):
    '''Upload docker-status to GoogleAppEngine'''
    child = pexpect.spawn('/application/google_appengine/appcfg.py --email {} '
        '{}'.format(env['GOOGLE_EMAIL'], cmd), timeout=timeout)
    child.logfile_read = sys.stdout
    try:
        child.expect('Password .*:', timeout=3)
        child.sendline(env['GOOGLE_PASSWORD'])
    except:
        pass
    return child.expect(pexpect.EOF)


def main():
    '''Deploy docker-status into GoogleAppEngine'''

    # Deploy application
    setup_check()
    gae_api('update {}'.format(env['APP_PATH']))
    gae_api('set_default_version {}'.format(env['APP_PATH']), timeout=15)
    time.sleep(15)     # Let new version become available


if __name__ == '__main__':
    main()

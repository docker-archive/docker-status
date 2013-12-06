#!/usr/bin/env python
'''Check docker-status services'''

import json
import toolkit
import urllib2


if toolkit.deployment() == 'production':
    from gae.prodtool import call_api
else:
    from gae.devtool import call_api

services = {
    'index': 'https://index.docker.io/v1/_status',
    'registry': 'http://docker-status.dotcloud.com:5000/_status'}


def query_service(service, url):
    retval = ''
    try:
        r = urllib2.urlopen(url, timeout=15)
        retval = r.read()
    except urllib2.HTTPError as e:
        if service == 'registry' and e.code == 503:
            retval = e.read()
    except:
        pass
    return retval


def normalize_status(service, data):
    retval = data
    if service == 'index':
        retval = {'services': [], 'failures': {}}
        for key in data:
            if key == 'host':
                continue
            retval['services'].append(key)
            status = data[key].get('status', None)
            if status != 'ok':
                retval['failures'].update({key: data[key].get(
                    'message', 'unspecified')})
    retval['services'].sort()
    return retval


def api_data(service, data):
    '''Create stashboard status data'''
    if not data:
        return {'status': 'down', 'message': 'The server could not be reached'}
    try:
        d = normalize_status(service, json.loads(data))
        if d['failures']:
            retval = {'status': 'warning', 'message': data}
        else:
            retval = {'status': 'up', 'message':
                'Services {} running properly'.format(d['services'])}
    except Exception as e:
        retval = {'status': 'warning', 'message': str(e)}
    return retval


def check(service, url):
    data = api_data(service, query_service(service, url))
    call_api(service, data)


def main():
    for service in services:
        check(service, services[service])


if __name__ == '__main__':
    main()

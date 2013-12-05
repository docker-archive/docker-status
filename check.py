#!/usr/bin/env python
'''Check docker-status services'''

import json
import oauth2 as oauth
import urllib
import urllib2
import toolkit

server_url = ('https://docker-status.appspot.com' if
    toolkit.deployment() == 'production' else 'http://localhost:8080')

# Base url for stashboard API requests
base_url = '{}/admin/api/v1'.format(server_url)

# Oauth credentials
consumer_key = ''
consumer_secret = ''
oauth_key = ''
oauth_secret = ''

# Authenticate with stashboard
consumer = oauth.Consumer(key=consumer_key, secret=consumer_secret)
token = oauth.Token(oauth_key, oauth_secret)
client = oauth.Client(consumer, token=token)

# Dynamically find docker-status services
# services = http://localhost:8080/admin/api/v1/services

services = {
    'index': 'https://index.docker.io/v1/_status',
    'registry': 'http://docker-status.dotcloud.com:5000/_status'}


def call_api(service, data):
    '''Submit service status to API'''
    api_url = '{}/services/{}/events'.format(base_url, service)
    print json.dumps(data, sort_keys=True, skipkeys=True)
    client.request(api_url, "POST", body=urllib.urlencode(data))


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


def check(service, url):
    data = {'status': 'up', 'message': 'docker {} services are running'.format(
        service)}
    try:
        r = urllib2.urlopen(url, timeout=15)
        if r.getcode() >= 300:
            data = {'status': 'warning', 'message': json.loads(r.read())}
    except Exception as e:
        if e.getcode() == 503:
            data = {'status': 'warning', 'message': json.loads(e.read())}
        else:
            data = {'status': 'down',
                'message': 'The server could not be reached.'}
    call_api(service, data)


def main():
    for service in services:
        check(service, services[service])


if __name__ == '__main__':
    main()

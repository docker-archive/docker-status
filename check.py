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

services = [
    {'name': 'index', 'url': 'https://index.docker.io/v1/_status'},
    {'name': 'registry',
        'url': 'http://docker-status.dotcloud.com:5000/_status'}]


def call_api(service, data):
    '''Submit service status to  API'''
    api_url = '{}/services/{}/events'.format(base_url, service)
    print json.dumps(data)
    client.request(api_url, "POST", body=urllib.urlencode(data))


def warning_status(status_dict, msg=''):
    d = json.loads(status_dict)
    for key in d:
        status = d[key].get('status', None)
        if status not in ('ok', None):
            msg += '{}: {}. '.format(key, d[key]['message'])
    return {'status': 'warning', 'message': msg}


def check(service, url):
    print 'Checking ' + service + ' (' + url + ')'
    data = {'status': 'down',
        'message': 'The server could not be reached.'}
    try:
        r = urllib2.urlopen(url, timeout=30)
        if r.getcode() >= 300:
            data = warning_status(r.read())
        else:
            data = {'status': 'up', 'message':
                'Docker {} services are responding.'.format(service)}
    except Exception as e:
        if e.getcode() == 500:
            data = warning_status(e.read())
    call_api(service, data)


def main():
    for service in services:
        check(service['name'], service['url'])


if __name__ == '__main__':
    main()


'''Check docker-status services'''

import requests

docker_status_server = 'localhost'

# Base url for stashboard rest requests
base_url = 'http://{}:8080/admin/api/v1'.format(docker_status_server)

# Dynamically find docker-status services
# services = http://localhost:8080/admin/api/v1/services

services = [
    {'name': 'index', 'url': 'https://index.docker.io/v1/_status/' },
    {'name': 'registry', 'url': 'https://registry.docker.io/_health/' } ]

def call_api(service, data):
    '''Submit service status to  API. No verification attempted'''
    requests.post(base_url + '/services/{}/events'.format(service), data)

def check(service, url):
    print 'Checking ' + service + ' (' + url + ')'

    try:
        data = { 'status': 'down',
                 'message': 'The server could not be reached.' }
        r = requests.get(url, headers={
            'Cache-Control': 'max-age=30'}, timeout=30)
        if r.status_code == 200:
            data = {'status': 'up',
                    'message': 'The server is responding.' }
    except:
        pass
    call_api(service, data)

for service in services:
    check(service['name'], service['url'])

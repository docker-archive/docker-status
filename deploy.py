#!/usr/bin/env python
'''Deploy docker-status service monitoring docker registry and index

      ./deploy.py'''

import oauth2 as oauth
import json
import urllib
import random
import shutil
import requests
import tempfile
import os
import time
from fabric import api
from fabric.api import run, sudo, warn_only
from subprocess import call

app_id = "docker-status"    # Stashboard application id
docker_status_server = 'docker-status.dotcloud.com'
services = ['registry', 'index']
repository = 'mzdaniel/{}'.format(app_id)
data_repository = 'mzdaniel/data'
data_dockerfile_url = ( 'http://raw.github.com/dotcloud/docker/master/'
    'contrib/desktop-integration/data/Dockerfile' )

# OAuth keys
consumer_key = 'anonymous'
consumer_secret = 'anonymous'
oauth_key = 'ACCESS_TOKEN'
oauth_secret = 'ACCESS_SECRET'
admin_login = 'test@example.com'

# Prepare fabric
api.env.host_string = docker_status_server
api.env.user = 'root'
api.env.key_filename = '/home/daniel/.ssh/dotcloud-dev.pem'


def retry(func,args=[],kwargs={},sleep=0,count=5,hide_exc=False,
 func_success=lambda x:True):
    '''Return func(args) after count tries if not exception and func_success'''
    for i in range(count):
        if i: time.sleep(sleep)
        try:
            retval = func(*args,**kwargs)
            if func_success(retval):
                return retval
        except Exception, exc:
            pass
    if not hide_exc: raise exc


def init_docker_status():
    '''Initialize docker-status with docker registry service'''

    # Create stashboard client.
    consumer = oauth.Consumer(key=consumer_key, secret=consumer_secret)
    token = oauth.Token(oauth_key, oauth_secret)
    client = oauth.Client(consumer, token=token)

    # Stashboard API base url for all rest requests
    base_url = "http://{}/admin/api/v1".format(docker_status_server)

    # Login as admin prompts stashboard to initialize itself
    r = requests.session()

    login_str = ( 'http://{0}/_ah/login?email={1}&admin=True&action=Login&'
        'continue=http://{0}/admin'.format(docker_status_server, admin_login) )
    retry(r.get, [login_str], sleep=2)
    retry(r.get, ['http://{}/admin'.format(docker_status_server)], sleep=2)
    retry(r.post,['http://{}/admin/setup'.format(docker_status_server)], sleep=2)

    # Create new services
    services_json = {}
    for service in services:
        data = urllib.urlencode({
            'name': service,
            'description': '"Docker {} service"'.format(service) })
        resp, content = client.request(base_url + '/services', 'POST', body=data)
        services_json[service] = json.loads(content)

    # GET the list of possible status images
    resp, content = client.request(base_url + "/status-images", "GET")
    data = json.loads(content)
    images = data["images"]

    # Pick a random image for our status
    image = random.choice(images)

    # POST to the Statuses Resources to create a new Status
    data = urllib.urlencode({
        "name": "Maintenance",
        "description": "The web service is under-going maintenance",
        "image": image["name"],
        "level": "WARNING",
    })

    resp, content = client.request(base_url + "/statuses", "POST", body=data)
    status = json.loads(content)

    # Ensure the new maintenance status gets updated
    retry(client.request, [base_url + '/statuses/maintenance', 'GET'], sleep=1,
        func_success=lambda x: x[0].get('status') == '200')

    # Initialize all services with maintenance status
    for service in services_json:
        data = urllib.urlencode({
            "message": "Initial maintenance event",
            "status": status["id"].lower() })
        resp, content = client.request('{}/events'.format(
            services_json[service]['url']), "POST", body=data)

# Build docker-status container
tmp_dir = tempfile.mkdtemp(dir='.')
os.chdir(tmp_dir)
call('cp ../Dockerfile .', shell=True)
call('cp ../check.py .', shell=True)
call('docker build -t {} .'.format(repository), shell=True)
call('wget {}'.format(data_dockerfile_url), shell=True)
call('docker build -t {} .'.format(data_repository), shell=True)
os.chdir('..')
shutil.rmtree(tmp_dir)

# Push container and data container to the index
call('docker push {}'.format(repository), shell=True)
call('docker push {}'.format(data_repository), shell=True)

# pull container
run('docker pull {}'.format(repository))
run('docker pull {}'.format(data_repository))

# Ensure latest version of docker on docker-status server
sudo('apt-get update -q; apt-get install -y lxc-docker')

# Create an empty data container
try:
    run('docker run -name {}-data {} true'.format(app_id, data_repository))
except:
    with warn_only():
        run('docker rm {}-data'.format(app_id))
        run('docker run -name {}-data {} true'.format(app_id, data_repository))

# setup host and launch docker-status container
run('for id in $(docker ps  |cut -d" " -f1 | sed 1d -); do '
    '  if docker inspect $id | grep -q \'"Image": "{}",\'; then '
    '     docker kill $id; fi  ; done'.format(repository))
sudo('cat >/etc/init/{0}.conf <<-EOF\n'
    'description "Docker status service"\n'
    'author "Daniel Mizyrycki"\n'
    'start on filesystem and started lxc-net and started docker\n'
    'stop on runlevel [!2345]\n'
    'respawn\n'
    'exec /usr/bin/docker run -volumes-from {0}-data -p 80:8080 -p 8000:8000 {1}\n'
    'EOF\n'.format(app_id, repository))
sudo('if ! start {0}; then restart {0}; fi'.format(app_id))

# initialize docker-status
init_docker_status()

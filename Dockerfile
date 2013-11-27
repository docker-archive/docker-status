# VERSION:        0.1.5
# AUTHOR:         Daniel Mizyrycki <daniel@docker.com>
# DESCRIPTION:    Build docker-status container
# URLS:           stashboard page:       http://127.0.0.1
#                 stashboard admin page: http://127.0.0.1/admin
#
# TO_BUILD:   docker build -t docker-status -rm .
# USAGE:
#   # Download docker-status and data Dockerfiles
#   wget https://raw.github.com/dotcloud/docker/docker-status/hack/infrastructure/docker-status/Dockerfile
#   wget http://raw.github.com/dotcloud/docker/master/contrib/desktop-integration/data/Dockerfile
#
#   # Local ephemeral run  (data not saved after server container exits)
#   docker run -p 127.0.0.1:80:8080 -p 127.0.0.1:8000:8000 docker-status
#
#   # remote access ephemeral run (server container process remote queries)
#   docker run -p 80:8080 -p 8000:8000 docker-status
#
#   # stateful remote access (data is kept on a data container)
#   docker run -name docker-status-data data true   # Create data container
#   docker run -volumes-from docker-status-data -p 80:8080 -p 8000:8000 docker-status

DOCKER-VERSION 0.6.6

# Base docker image
FROM ubuntu:12.04
MAINTAINER Daniel Mizyrycki <daniel@docker.com>

RUN echo 'deb http://archive.ubuntu.com/ubuntu precise main universe' > \
  /etc/apt/sources.list
RUN apt-get update -q
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y less wget bzip2 unzip \
  python-pip ca-certificates cron supervisor
RUN pip install --install-option="--install-lib=/usr/lib/python2.7" requests pyyaml

# Install stashboard and its dependencies
RUN mkdir /application; cd /application; \
  wget -q http://googleappengine.googlecode.com/files/google_appengine_1.8.7.zip; \
  unzip -q /application/google_appengine_1.8.7.zip; rm google_appengine_1.8.7.zip
RUN cd /application; wget -q -O - http://github.com/twilio/stashboard/tarball/master | \
    tar -zx --transform 's/[^\/]*/stashboard/'

# Add check worker
ADD check.py /application/stashboard/stashboard/check.py

# Create sysadmin account for /data directory
RUN useradd -m -d /data sysadmin

# Setup check worker service
RUN echo '*/5 * * * * python /application/stashboard/stashboard/check.py' > \
  /var/spool/cron/crontabs/root; chmod 600 /var/spool/cron/crontabs/root
RUN /bin/echo -e "\
[program:cron]\n\
command=/usr/sbin/cron -f\n" >  /etc/supervisor/conf.d/cron.conf

# Setup docker-status web service
# Add docker-status check endpoint
RUN sed -Ei 's/- url: \.\*/- url: \/check\n  script: check.py\n\
  secure: optional\n\n- url: \.\*/' /application/stashboard/stashboard/app.yaml
RUN /bin/echo -e "\
[program:status]\n\
command=/application/google_appengine/dev_appserver.py --skip_sdk_update_check\
 --host 0.0.0.0 --port 8080 --admin_host 0.0.0.0 --datastore_path=/data/docker-status.db\
 /application/stashboard/stashboard/app.yaml\n\
directory=/data\n\
user=sysadmin\n" >  /etc/supervisor/conf.d/status.conf

CMD ["/usr/bin/supervisord", "-n"]

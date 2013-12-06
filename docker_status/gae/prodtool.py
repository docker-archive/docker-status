import json
from models import Status, Service, Event


def call_api(service, data):
    '''Submit service status to API'''
    service = Service.get_by_slug(service)
    status = Status.get_by_slug(data['status'])
    e = Event(service=service, status=status, message=data['message'])
    print json.dumps(data, sort_keys=True, skipkeys=True)
    e.put()

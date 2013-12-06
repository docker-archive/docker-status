import json
import oauth2 as oauth
import urllib


def call_api(service, data):
    '''Submit service status to API'''
    consumer_key = ''
    consumer_secret = ''
    oauth_key = ''
    oauth_secret = ''
    api_url = ('http://localhost:8080/admin/api/v1/services/{}/events'.
        format(service))

    # Authenticate with stashboard
    consumer = oauth.Consumer(key=consumer_key, secret=consumer_secret)
    token = oauth.Token(oauth_key, oauth_secret)
    client = oauth.Client(consumer, token=token)

    print json.dumps(data, sort_keys=True, skipkeys=True)
    client.request(api_url, "POST", body=urllib.urlencode(data))

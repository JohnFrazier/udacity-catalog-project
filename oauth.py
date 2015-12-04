import json
import httplib2
import string
import random


fb_user_info_fields = ('username', 'provider', 'email', 'fb_id', 'picture')
fb_client_secrets_path = 'fb_clients_secrets.json'

fb_access_url_base = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token'
fb_basic_request_url_f = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email'
fb_pict_request_url_f = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0%height=200&width=200'


def _getAsJSON(url):
    with httplib2.Http() as h:
        return json.loads(h.request(url, 'GET')[1])


def generateStateString():
    '''generate a random string for session state'''
    return ''.join(
        random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))


def getUserDataFB(request_token):
    '''return a dict with user info from a fb request payload'''
    # ret dict contains 'error' key on fail.
    ret = {'provider': 'facebook'}

    somesecrets = json.loads(open(fb_client_secrets_path, 'r').read())
    app_id = somesecrets['web']['app_id']
    app_secret = somesecrets['web']['app_secret']
    del somesecrets
    access_url = str.join((
        fb_access_url_base.app,
        'client_id=%s' % app_id,
        'client_secret=%s' % app_secret,
        'fb_exchange_token=%s' % request_token), '&')

    # get token
    with httplib2.Http() as h:
        access_result = h.request(access_url, 'GET')[1]
    token = access_result.split('&')[0]

    # get basic user info
    data = _getAsJSON(fb_basic_request_url_f % token)
    ret['username'] = data['name']
    ret['email'] = data['email']
    ret['facebook_id'] = data['id']

    # get picture url
    data = _getAsJSON(fb_pict_request_url_f % token)
    ret['picture'] = data['data']['url']

    return ret

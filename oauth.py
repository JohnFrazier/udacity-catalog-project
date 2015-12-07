import json
import httplib2
import string
import random


fb_user_info_fields = ('username', 'provider', 'email', 'fb_id', 'picture')
fb_client_secrets_path = 'secrets/fb_client_secrets.json'
fb_access_url_base = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token'
fb_basic_request_url_f = 'https://graph.facebook.com/v2.5/me?%s&fields=name,id,email'
fb_picture_request_url_f = 'https://graph.facebook.com/v2.5/me/picture?%s&redirect=0&height=200&width=200'


def _getAsJSON(url):
    h = httplib2.Http()
    s = h.request(url, 'GET')
    if s[0]['status'] == '400':
        print "json request failed %s" % url
        return None
    return json.loads(s[1])


def generateStateString():
    '''generate a random string for session state'''
    return ''.join(
        random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))


def getUserDataFB(request):
    '''return a dict with user info from a fb request payload'''
    # ret dict contains 'error' key on fail.
    ret = {'provider': 'facebook'}

    somesecrets = json.loads(open(fb_client_secrets_path, 'r').read())
    app_id = somesecrets['web']['app_id']
    app_secret = somesecrets['web']['app_secret']
    del somesecrets
    access_url = "&".join((
        fb_access_url_base,
        'client_id=%s' % app_id,
        'client_secret=%s' % app_secret,
        'fb_exchange_token=%s' % request.data))

    # get token
    h = httplib2.Http()
    access_result = h.request(access_url, 'GET')
    if access_result[0]['status'] == '400':
        return dict(error="nothign to see here")

    token = access_result[1].split('&')[0]
    print token
    # get basic user info
    data = _getAsJSON(fb_basic_request_url_f % token)
    if not data:
        ret['error'] = "fb basic user request failed"
        return ret
    ret['username'] = data['name']
    ret['email'] = data['email']
    ret['facebook_id'] = data['id']

    # get picture url
    data = _getAsJSON(fb_picture_request_url_f % token)
    if not data:
        ret['error'] = "fb picture request failed"
        return ret
    ret['picture'] = data['data']['url']

    return ret

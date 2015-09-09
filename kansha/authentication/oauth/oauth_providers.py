# -*- coding:utf-8 -*-
#--
# Copyright (c) 2012-2014 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import json
import urllib
import urllib2
import urlparse

import oauth2 as oauth

from nagare import presentation


class OAuth1(object):
    name = 'OAuth1 provider'

    def __init__(self, key, secret, scopes=(), timeout=None):
        self.consumer = oauth.Consumer(key, secret)
        self.timeout = timeout
        self.scopes = scopes
        self.token = None

    def fetch(self, url, post=False, **kw):
        client = oauth.Client(self.consumer, self.token, None, self.timeout)
        headers, data = client.request(url,
                                       method='POST' if post else 'GET',
                                       body=urllib.urlencode(kw))
        if headers['content-type'].startswith(('application/json', 'text/javascript')):
            data = json.loads(data)

        return data

    def get_auth_url(self, callback_url, **kw):
        self.token = None
        data = self.fetch(self.request_token_endpoint,
                          oauth_callback=callback_url,
                          post=True, **kw)
        self.token = oauth.Token.from_string(data)
        return (self.authorization_endpoint + '?' +
                urllib.urlencode({'oauth_token': self.token.key}))

    def get_token(self, token, verifier):
        if not token:
            return None

        if verifier:
            self.token.set_verifier(verifier)
        data = self.fetch(self.token_endpoint, post=True)
        self.token = oauth.Token.from_string(data)
        return self

    def get_raw_profile(self):
        return self.fetch(self.profile_endpoint)

    def get_profile(self):
        return {}, self.get_raw_profile()


@presentation.render_for(OAuth1)
def render(self, h, comp, *args):
    action = lambda request, response: comp.answer(self.get_token(request.params.get('oauth_token'), request.params.get('oauth_verifier')))
    callback = h.a.action(action, with_request=True).get('href')

    h.response.status = 301
    h.response.headers['location'] = self.get_auth_url(h.request.relative_url(callback))
    return ''

# -----------------------------------------------------------------------------


class OAuth2(object):
    name = 'OAuth2 provider'

    def __init__(self, key, secret, scopes=(), timeout=None):
        self.key = key
        self.secret = secret
        self.scopes = scopes
        self.timeout = timeout

        self.callback_url = self.code = self.access_token = None

    def fetch(self, url, post=False, headers=None, **kw):
        params = urllib.urlencode(kw)
        if params and not post:
            url += ('?' + params)

        request = urllib2.Request(url, params if post else None, headers or {})

        if self.timeout:
            response = urllib2.urlopen(request, timeout=self.timeout)
        else:
            response = urllib2.urlopen(request)

        content_type = response.info().getheader('content-type').split(';')[0]
        data = response.read()
        response.close()

        if response.getcode() != 200:
            return None
        return json.loads(data)if content_type in ('application/json', 'text/javascript') else dict(urlparse.parse_qsl(data))

    def get_auth_url(self, callback_url, **kw):
        self.callback_url = callback_url

        kw['client_id'] = self.key
        kw['redirect_uri'] = callback_url
        if self.scopes:
            kw['scope'] = ' '.join(self.scopes)
        return '%s?%s' % (self.authorization_endpoint, urllib.urlencode(kw))

    def extract_token(self, code):
        if not code:
            return None
        self.code = code
        self.access_token = self.get_token(code)
        return self

    def get_token(self, code, **kw):
        response = self.fetch(
            self.token_endpoint,
            code=code,
            client_id=self.key, client_secret=self.secret,
            redirect_uri=self.callback_url, post=True, **kw
        )
        return response['access_token']  # , response.get('refresh_token')

    def get_raw_profile(self):
        return self.fetch(self.profile_endpoint, access_token=self.access_token)

    def get_profile(self):
        return {}, self.get_raw_profile()


@presentation.render_for(OAuth2)
def render(self, h, comp, *args):
    action = lambda request, response: comp.answer(self.extract_token(request.params.get('code')))
    callback = h.a.action(action, with_request=True).get('href')
    callback, state = callback.split('/?')
    print state
    h.response.status = 301
    h.response.headers['location'] = self.get_auth_url(h.request.relative_url(callback), state=state)
    return ''

# -----------------------------------------------------------------------------


class OpenIDConnect(OAuth2):
    name = 'OpenID connect provider'

    def get_auth_url(self, callback_url, **kw):
        return super(OpenIDConnect, self).get_auth_url(callback_url, response_type='code', **kw)

    def get_token(self, code):
        return super(OpenIDConnect, self).get_token(code, grant_type='authorization_code')

# -----------------------------------------------------------------------------


class Google(OpenIDConnect):
    name = 'google'

    authorization_endpoint = 'https://accounts.google.com/o/oauth2/auth'
    token_endpoint = 'https://accounts.google.com/o/oauth2/token'

    profile_endpoint = 'https://www.googleapis.com/oauth2/v1/userinfo'

    def __init__(self, key, secret, scopes=(), offline=False, prompt=False):
        super(Google, self).__init__(key, secret, ('openid',) + tuple(scopes))

        self.offline = offline
        self.prompt = prompt

    def fetch(self, url, post=False, **kw):
        response = super(Google, self).fetch(url, post=post, **kw)
        error = response.get('error')
        if error:
            raise IOError(error)

        return response

    def get_auth_url(self, callback_url, **kw):
        return super(Google, self).get_auth_url(
            callback_url,
            access_type='offline' if self.offline else 'online',
            approval_prompt='force' if self.prompt else 'auto',
            **kw
        )

    def get_profile(self):
        _, profile = super(Google, self).get_profile()
        return {
            'id': profile['id'],
            'name': profile.get('name', profile['email']),
            'email': profile.get('email'),
            'picture': profile.get('picture', None)
        }, profile


class Twitter(OAuth1):
    name = 'twitter'

    request_token_endpoint = 'https://api.twitter.com/oauth/request_token'
    authorization_endpoint = 'https://api.twitter.com/oauth/authorize'
    token_endpoint = 'https://api.twitter.com/oauth/access_token'

    profile_endpoint = 'https://api.twitter.com/1.1/account/verify_credentials.json'

    def get_profile(self):
        _, profile = super(Twitter, self).get_profile()
        return {
            'id': profile['id_str'],
            'name': profile['name'],
            'email': profile.get('email'),
            'picture': profile['profile_image_url_https']
        }, profile


class Facebook(OAuth2):
    name = 'facebook'

    authorization_endpoint = 'https://www.facebook.com/dialog/oauth'
    token_endpoint = 'https://graph.facebook.com/oauth/access_token'

    profile_endpoint = 'https://graph.facebook.com/me'

    # def __init__(self, key, secret, scopes=()):
    #     scopes = ['public_profile' if s == 'profile' else s for s in scopes]
    #     super(Facebook, self).__init__(key, secret, scopes)

    def get_raw_profile(self):
        return self.fetch(self.profile_endpoint, access_token=self.access_token, fields='id,name,email')

    def get_profile(self):

        _, profile = super(Facebook, self).get_profile()
        return {
            'id': profile['id'],
            'name': profile['name'],
            'email': profile.get('email'),
            'picture': self.get_picture_url()
        }, profile

    def get_picture_url(self):
        """Get URL picture"""
        profile_picture = self.fetch(self.profile_endpoint, post=False,
                                     fields='picture', access_token=self.access_token)
        if not(profile_picture['picture']['data']['is_silhouette']):
            return profile_picture['picture']['data']['url']
        else:
            return None


class Github(OAuth2):
    name = 'github'

    authorization_endpoint = 'https://github.com/login/oauth/authorize'
    token_endpoint = 'https://github.com/login/oauth/access_token'

    profile_endpoint = 'https://api.github.com/user'
    email_endpoint = 'https://api.github.com/user/emails'

    def get_email(self):
        resp = self.fetch(self.email_endpoint, post=False,
                             access_token=self.access_token)
        for email in resp:
            if email['primary']:
                return email['email']
        return ''

    def get_profile(self):
        _, profile = super(Github, self).get_profile()
        return {
            'id': str(profile['id']),
            'name': profile['name'],
            'email': self.get_email(),
            'picture': profile['avatar_url']
        }, profile


class Dropbox(OAuth1):
    name = 'dropbox'

    request_token_endpoint = 'https://api.dropbox.com/1/oauth/request_token'
    authorization_endpoint = 'https://www.dropbox.com/1/oauth/authorize'
    token_endpoint = 'https://api.dropbox.com/1/oauth/access_token'

    profile_endpoint = 'https://api.dropbox.com/1/account/info'

    def get_auth_url(self, callback_url):
        return super(Dropbox, self).get_auth_url(callback_url) + '&' + urllib.urlencode({'oauth_callback': callback_url})

    def get_profile(self):
        _, profile = super(Dropbox, self).get_profile()
        return {
            'id': str(profile['uid']),
            'name': profile['display_name'],
            'email': profile['email'],
            'picture': None
        }, profile


class Salesforce(OpenIDConnect):
    name = 'salesforce'

    authorization_endpoint = 'https://login.salesforce.com/services/oauth2/authorize'
    token_endpoint = 'https://login.salesforce.com/services/oauth2/token'

    def fetch(self, url, post=False, headers=None, **kw):
        data = super(Salesforce, self).fetch(url, post=post, headers=headers, **kw)
        self.profile_endpoint = data['id']
        return data

    def get_raw_profile(self):
        return self.fetch(self.profile_endpoint, headers={'Authorization': 'Bearer ' + self.access_token})

    def get_profile(self):
        _, profile = super(Salesforce, self).get_profile()
        return {
            'id': profile['user_id'],
            'name': profile['display_name'],
            'email': profile['email'],
            'picture': profile['photos']['picture']
        }, profile


class Flickr(OAuth1):
    name = 'flickr'

    request_token_endpoint = 'http://www.flickr.com/services/oauth/request_token'
    authorization_endpoint = 'http://www.flickr.com/services/oauth/authorize'
    token_endpoint = 'http://www.flickr.com/services/oauth/access_token'

    profile_endpoint = 'http://api.flickr.com/services/rest?method=flickr.test.login&format=json&nojsoncallback=1'

    def get_auth_url(self, callback_url):
        return super(Flickr, self).get_auth_url(callback_url) + '&perms=read'

    def get_raw_profile(self):
        user_id = super(Flickr, self).get_raw_profile()['user']['id']
        return self.fetch('http://api.flickr.com/services/rest?method=flickr.people.getInfo&format=json&nojsoncallback=1&user_id=' + user_id)

    def get_profile(self):
        _, profile = super(Flickr, self).get_profile()
        profile = profile['person']

        iconfarm = profile['iconfarm']
        iconserver = profile['iconserver']
        picture = 'http://farm%d.staticflickr.com/%s/buddyicons/%s.jpg' % (iconfarm, iconserver, profile['nsid'])

        return {
            'id': profile['id'],
            'name': profile['realname']['_content'] or profile['username']['_content'],
            'email': None,
            'picture': picture if (iconfarm or iconserver) else None
        }, profile


class Vimeo(OAuth1):
    name = 'vimeo'

    request_token_endpoint = 'https://vimeo.com/oauth/request_token'
    authorization_endpoint = 'https://vimeo.com/oauth/authorize'
    token_endpoint = 'https://vimeo.com/oauth/access_token'

    profile_endpoint = 'http://vimeo.com/api/rest/v2?method=vimeo.people.getInfo&format=json'

    def get_profile(self):
        _, profile = super(Vimeo, self).get_profile()
        profile = profile['person']
        return {
            'id': profile['id'],
            'name': profile['display_name'],
            'email': None,
            'picture': profile['portraits']['portrait'][1]['_content']
        }, profile


class Bitbucket(OAuth1):
    name = 'bitbucket'

    request_token_endpoint = 'https://bitbucket.org/!api/1.0/oauth/request_token'
    authorization_endpoint = 'https://bitbucket.org/!api/1.0/oauth/authenticate'
    token_endpoint = 'https://bitbucket.org/!api/1.0/oauth/access_token'

    profile_endpoint = 'https://api.bitbucket.org/1.0/user'

    def get_profile(self):
        _, profile = super(Bitbucket, self).get_profile()
        profile = profile['user']
        return {
            'id': profile['resource_uri'],
            'name': profile['first_name'] + ' ' + profile['last_name'],
            'email': None,
            'picture': profile['avatar']
        }, profile


class Yahoo(OAuth1):
    name = 'yahoo'

    request_token_endpoint = 'https://api.login.yahoo.com/oauth/v2/get_request_token'
    authorization_endpoint = 'https://api.login.yahoo.com/oauth/v2/request_auth'
    token_endpoint = 'https://api.login.yahoo.com/oauth/v2/get_token'

    profile_endpoint = 'http://social.yahooapis.com/v1/me/guid?format=json'

    def get_raw_profile(self):
        user_id = super(Yahoo, self).get_raw_profile()['guid']['value']
        return self.fetch('http://social.yahooapis.com/v1/user/%s/profile?format=json' % user_id)

    def get_profile(self):
        _, profile = super(Yahoo, self).get_profile()
        profile = profile['profile']

        given_name = profile.get('givenName', '')
        family_name = profile.get('familyName', '')
        emails = profile.get('emails')

        return {
            'id': profile['guid'],
            'name': ' '.join((given_name, family_name)) if (given_name or family_name) else profile['nickname'],
            'email': emails[0]['handle'] if emails else None,
            'picture': profile['image']['imageUrl']
        }, profile


class Dailymotion(OpenIDConnect):
    name = 'dailymotion'

    authorization_endpoint = 'https://api.dailymotion.com/oauth/authorize'
    token_endpoint = 'https://api.dailymotion.com/oauth/token'

    def fetch(self, url, post=False, headers=None, **kw):
        data = super(Dailymotion, self).fetch(url, post=post, headers=headers, **kw)
        self.user_id = data.get('uid')
        return data

    def get_raw_profile(self):
        return self.fetch('https://api.dailymotion.com/user/' + self.user_id)

    def get_profile(self):
        _, profile = super(Dailymotion, self).get_profile()
        return {
            'id': str(profile['id']),
            'name': profile['screenname'],
            'email': None,
            'picture': None
        }, profile


class Viadeo(OpenIDConnect):
    name = 'viadeo'

    authorization_endpoint = 'https://secure.viadeo.com/oauth-provider/authorize2'
    token_endpoint = 'https://secure.viadeo.com/oauth-provider/access_token2'

    profile_endpoint = 'https://api.viadeo.com/me'

    def get_profile(self):
        _, profile = super(Viadeo, self).get_profile()
        return {
            'id': str(profile['id']),
            'name': profile['name'],
            'email': None,
            'picture': profile['picture_small'] if profile['has_picture'] else None
        }, profile


class Linkedin(OAuth1):
    name = 'linkedin'

    request_token_endpoint = 'https://api.linkedin.com/uas/oauth/requestToken'
    authorization_endpoint = 'https://api.linkedin.com/uas/oauth/authorize'
    token_endpoint = 'https://api.linkedin.com/uas/oauth/accessToken'

    profile_endpoint = 'http://api.linkedin.com/v1/people/~:(id,firstName,lastName,email-address,picture-url)?format=json'

    def get_auth_url(self, callback_url):
        return super(Linkedin, self).get_auth_url(callback_url.replace('&', ';'), scope=' '.join(self.scopes))

    def get_profile(self):
        _, profile = super(Linkedin, self).get_profile()
        return {
            'id': profile['id'],
            'name': profile['firstName'] + ' ' + profile['lastName'],
            'email': profile['emailAddress'],
            'picture': profile['pictureUrl']
        }, profile


class Foursquare(OpenIDConnect):
    name = 'foursquare'

    authorization_endpoint = 'https://foursquare.com/oauth2/authenticate'
    token_endpoint = 'https://foursquare.com/oauth2/access_token'

    profile_endpoint = 'https://api.foursquare.com/v2/users/self'

    def get_raw_profile(self):
        return self.fetch(self.profile_endpoint, oauth_token=self.access_token, v='20121130')

    def get_profile(self):
        _, profile = super(Foursquare, self).get_profile()
        profile = profile['response']['user']
        return {
            'id': profile['id'],
            'name': profile['firstName'] + ' ' + profile['lastName'],
            'email': profile['contact']['email'],
            'picture': '%s36x36%s' % (profile['photo']['prefix'], profile['photo']['suffix'])
        }, profile


class Instagram(OpenIDConnect):
    name = 'instagram'

    authorization_endpoint = 'https://api.instagram.com/oauth/authorize'
    token_endpoint = 'https://api.instagram.com/oauth/access_token'

    def __init__(self, key, secret, scopes=(), timeout=None):
        super(Instagram, self).__init__(key, secret, scopes, timeout)
        self.user = {}

    def fetch(self, url, post=False, headers=None, **kw):
        data = super(Instagram, self).fetch(url, post=post, headers=headers, **kw)
        if 'user' in data:
            self.user = data['user']
        return data

    def get_profile(self):
        return {
            'id': self.user['id'],
            'name': self.user['full_name'],
            'email': None,
            'picture': self.user['profile_picture']
        }, self.user

"""
# Too limited requests rate

class Reddit(OpenIDConnect):
    name = 'reddit'

    authorization_endpoint = 'https://ssl.reddit.com/api/v1/authorize'
    token_endpoint = 'https://ssl.reddit.com/api/v1/access_token'

    def __init__(self, key, secret, scopes=(), offline=False, prompt=False):
        super(Reddit, self).__init__(key, secret, ('identity',) + scopes)
"""

providers = dict([(provider.name, provider) for provider in (
    Google,
    Twitter,
    Facebook,
    Github,
    Dropbox,
    Salesforce,
    Flickr,
    Vimeo,
    Bitbucket,
    Yahoo,
    Dailymotion,
    Viadeo,
    Linkedin,
    Foursquare,
    Instagram
)])

# -----------------------------------------------------------------------------


class Middleware(object):

    def __init__(self, app, options, config_filename, config, error):
        self.app = app

    def __call__(self, environ, start_response):
        params = dict(urlparse.parse_qsl(environ['QUERY_STRING']))
        print params
        if ('state' in params):
            environ['QUERY_STRING'] += ('&' + params['state'])

        return self.app(environ, start_response)

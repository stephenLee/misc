import os
import base64
import logging

from urllib import urlencode
from urllib import quote
from urlparse import parse_qs

# import any json.py

try:
    import simplejson as json
except ImportError:
    try:
        from django.utils import simplejson as json
    except ImportError:
        import json

import webapp2
import jinja2

from google.appengine.api import urlfetch


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)



client_id = '357199909'
client_secret = '85cab851da0baf8ea08c13523355a504'
site = 'https://api.weibo.com/'
redirect_uri = 'http://www.example.com:8080/auth/weibo/callback'
authorization_url = 'oauth2/authorize'
token_url = 'oauth2/access_token'

class AuthHandler(webapp2.RequestHandler):
    def get_authorize_url(self, scope='', **kw):
        """
        Return the url to redirect the user for user content
        """
        client_id = self.get_consumer_info()[0]
        redirect_uri = self.get_callback_uri()
        site = self.get_site()
        authorization_url = self.get_authorization_url()
    
        oauth_params = {'redirect_uri': redirect_uri, 
                        'client_id': client_id, 'scope': scope}
        oauth_params.update(kw)
        return "%s%s?%s" % (site, quote(authorization_url), 
                            urlencode(oauth_params))

    def get_token(self, code, **kw):
        """
        Requests an access token
        """
        site = self.get_site()
        token_url = self.get_token_url()
        client_id, client_secret = self.get_consumer_info()
        redirect_uri = self.get_callback_uri()

        url = "%s%s" % (site, quote(token_url))
        data = {'redirect_uri': redirect_uri, 'client_id': client_id,
                'client_secret': client_secret, 'code': code}
        data.update(kw)
        
        http_headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        # post data
        result = urlfetch.fetch(url=url,
                                payload=urlencode(data),
                                method=urlfetch.POST,
                                headers=http_headers)
        content = json.loads(result.content)
        return content['access_token']

    def oauth2_init(self):
        authorization_url = self.get_authorize_url()
        self.redirect(authorization_url)

    def oauth2_callback(self):
        code = self.request.get('code')
        logging.info('code is %s' % code)
        access_token  = self.get_token(code)
        logging.info('access_token is %s' % access_token)
        self.redirect('/profile')
    
    def oauth2_request(self, token):
        """Makes an HTTP request with OAuth 2.0 access token using
           App Engine URLfetch API
        """
        return urlfetch.fetch(url.format(urlencode({'access_token': token}))).content

    def logout(self):
        self.redirect('/')

    def oauth2_error(self):
        self.redirect('/')
    
    def get_callback_uri(self):
        return redirect_uri
    
    def get_site(self):
        return site

    def get_authorization_url(self):
        return authorization_url
    
    def get_token_url(self):
        return token_url

    def get_consumer_info(self):
        return (client_id, client_secret)
    
class ProfileHandler(webapp2.RequestHandler):
    def get(self):
        if self.logged_in:
            self.render('profile.html', {
               'user': self.current_user, 
               'session': self.auth.get_user_by_session()})
        else:
            self.redirect('/')


    
class FrontHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render(self, template, **kw):
        self.write(render_str(template, **kw))

class MainPage(FrontHandler):
    def get(self):
        self.render("home.html")


app = webapp2.WSGIApplication([
        webapp2.Route(r'/', handler='weibo.MainPage', name='home'),
        webapp2.Route(r'/profile', handler='weibo.ProfileHandler', name='profile'),
        webapp2.Route(r'/auth/weibo', handler='weibo.AuthHandler:oauth2_init', name='auth-login'),
        webapp2.Route(r'/auth/weibo/callback', handler='weibo.AuthHandler:oauth2_callback', name='oauth-callback'),
        webapp2.Route(r'/logout', handler='weibo.AuthHandler:logout', name='logout')],
                              debug=True)

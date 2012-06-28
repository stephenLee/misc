import logging

from urllib import urlencode
# import any json.py

try:
    import simplejson as json
except ImportError:
    try:
        from django.utils import simplejson as json
    except ImportError:
        import json

URLS = ['https://api.weibo.com/oauth2/authorize?{0}', 'https://api.weibo.com/oauth2/access_token']

from google.appengine.api import urlfetch

class OAuth2Handler(object):
    def _oauth2_init(self, scope=''):
        """Initiates OAuth 2.0 dance.  
        """
        key, secret = self._get_consumer_info()
        callback_url = self._callback_uri()
        auth_url = URLS[0]
        if key and secret and auth_url and callback_url:
            params = { 'response_type': 'code', 'client_id': key, 'redirect_uri': callback_url }
            if scope:
                params.update(scope=scope)

            target_url = auth_url.format(urlencode(params)) 
            logging.debug('Redirecting user to %s' % target_url)

            self.redirect(target_url)
      
        else:
            logging.error('Something wrong!')
            self.redirect('/')
    
    def _oauth2_callback(self):
        """Step 2 of OAuth 2.0, whenever the user accepts or denies access."""
        code = self.request.get('code', None)
        logging.info('code is: %s' % code)
        error = self.request.get('error', None)
        callback_url = self._callback_uri()
        access_token_url = URLS[1]
        consumer_key, consumer_secret = self._get_consumer_info()
    
        if error:
            raise Exception(error)
      
        payload = {
            'code': code,
            'client_id': consumer_key,
            'client_secret': consumer_secret,
            'redirect_uri': callback_url,
            'grant_type': 'authorization_code'
        }
    
        resp = urlfetch.fetch(
            url=access_token_url, 
            payload=urlencode(payload), 
            method=urlfetch.POST,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
  
        auth_info = self._json_parser(resp.content)
        logging.info('auth_info is %s' % auth_info)
        user_data = getattr(self, '_get_weibo_user_info')(auth_info, uid='1748366623')
        logging.info('user_data is %s' % user_data)
        #should be implemented by the actual app
        self._on_sign_in(auth_info, user_data)
    
    def _get_weibo_user_info(self, auth_info, uid=''):
        """
        https://api.weibo.com/2/users/show.json
        """
        url  = 'https://api.weibo.com/2/users/show.json?uid=%s&{0}' % uid
        resp = self._oauth2_request(url, auth_info['access_token'])
        
        uinfo = json.loads(resp)
        uinfo.setdefault('link', 'http://weibo.com/%s' % uinfo['screen_name'])
        return uinfo

    def _callback_uri(self):
        """Returns a callback URL for a 2nd step of the auth process.
        Override this with something like:
      
        return self.uri_for('auth_callback',  _full=True)
        """
        return None
    
    def _get_consumer_info(self):
        """Should return a tuple (key, secret, desired_scopes).
        Defaults to None. You should redefine this method and return real values."""
        return (None, None, None)


    def _oauth2_request(self, url, token):
        """Makes an HTTP request with OAuth 2.0 access token using App Engine URLfetch API"""
        logging.info('access_token request url is: %s' % url.format(urlencode({'access_token': token})))
        return urlfetch.fetch(url.format(urlencode({'access_token':token}))).content


    def _json_parser(self, body):
        """Parses body string into JSON dict"""
        return json.loads(body)

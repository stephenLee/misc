import os

from oauth2 import OAuth2

import webapp2
import jinja2

client_id = '357199909'
client_secret = '85cab851da0baf8ea08c13523355a504'
root_url = 'https://api.weibo.com/'
authorization_url = 'oauth2/authorize'
token_url = 'oauth2/access_token'
redirect_uri = 'http://stephenlee.github.com'

oauth2_handler = OAuth2(client_id, client_secret, root_url, authorization_url, token_url)

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

def render_str(template, **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class WeiboHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render(self, template, **kw):
        self.write(render_str(template, **kw))

class MainPage(WeiboHandler):
    def get(self):
        self.render("home.html")

class AuthHandler(webapp2.RequestHandler):
    def oauth2_init(self, ):
        key, secret = self.get_consumer_info()
        authorization_url = oauth2_handler.authorize_url()
        self.redirect(authorization_url)

    def oauth2_callback(self, ):
        code = self.request.get('code')
        content = oauth2_handler.get_token(code)
        oauth2_client = requests.session(params={'access_token': content['access_token']})
        return oauth2_client

    def oauth2_error(self, ):
        self.redirect('/')

    def get_consumer_info(self):
        return (client_id, client_secret)
    
app = webapp2.WSGIApplication([('/', MainPage)])

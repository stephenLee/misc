import random
from string import letters

from webapp2 import WSGIApplication, Route

def make_secret_key(length=10):
    return ''.join(random.choice(letters) for unused in xrange(length))

secret_key = make_secret_key()

config = {}

config['webapp2_extras.sessions'] = {
    'secret_key': secret_key,
    }

config['webapp2_extras.auth'] = {
    'user_attributes': []
    }

# Map URLs to handlers
routes = [
    Route('/', handler='handlers.FrontHandler'),
    Route('/profile', handler='handlers.ProfileHandler', name='profile'),
    Route('/auth/renren', handler='handlers.AuthHandler:_oauth2_init',name='auth_login'),
    Route('/auth/renren/callback', handler='handlers.AuthHandler:_oauth2_callback', name='auth_callback'),
    Route('/logout', handler='handlers.LogoutHandler', name='logout')
    ]

app = WSGIApplication(routes, config=config, debug=True)

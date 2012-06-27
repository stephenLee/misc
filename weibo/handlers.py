import logging
import secrets

import webapp2
from webapp2_extras import auth, sessions, jinja2

from oauth2.handler import OAuth2Handler


def jinja2_factory(app):
    j = jinja2.Jinja2(app)
    j.environment.globals.update({
        # Set global variables.
          'uri_for': webapp2.uri_for
    })
    return j

class BaseHandler(webapp2.RequestHandler):
    def dispatch(self):
        # Get a session store for this request
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions
            self.session_store.save_sessions(self.response)
    
    #webapp2_cached_property decorator does two things:
    #Cache the value after the first time the property is accessed. 
    #(rather than recalculated it each time)
    #Converts the method into a property like using builtin @property
    #self.session['some_var']
    @webapp2.cached_property
    def session(self):
        """Returns a session using the default cookie key"""
        return self.session_store.get_session()

    @webapp2.cached_property
    def auth(self):
        return auth.get_auth()

    @webapp2.cached_property
    def user(self):
        """Returns currently logged in user"""
        user = self.auth.get_user_by_session()
        return user

    @webapp2.cached_property
    def user_model(self):
        user_model, timestamp = self.auth.store.user_model.get_by_auth_token(
            self.user['user_id'],
            self.user['token']) if self.user else (None, None)
        return user_model
    
    @webapp2.cached_property
    def jinja2(self):
        # Returns a jinja2 renderer cached in the app registry.
        return jinja2.get_jinja2(factory=jinja2_factory, app=self.app)

    def render_response(self, _template, **context):
        #Renders a template and writes the result to the response.
        ctx = {'user': self.user_model}
        ctx.update(context)
        rv = self.jinja2.render_template(_template, **ctx)
        self.response.write(rv)

class FrontHandler(BaseHandler):
    def get(self):
        """Handles home page"""
        self.render_response('home.html')

class Logout(BaseHandler):
    def get(self):
        """Destroy user session, redirect to front page"""
        self.auth.unset_session()
        self.redirect('/')

class AuthHandler(BaseHandler, OAuth2Handler):
    def _get_consumer_info(self):
        return (secrets.CLIENT_ID, secrets.CLIENT_SECRET)
    
    def _callback_uri(self):
        return self.uri_for('auth_callback', _full=True)


class ProfileHandler(BaseHandler):
    def get(self):
        """Handles GET /profile"""
        if self.user:
            self.render_response('profile.html',
                                 {'user': self.user_model, 
                                  'session': self.auth.get_user_by_session()})
        else:
            self.redirect('/')
            

#!/usr/bin/env python

# Copyright (c) 2009 Johan Uhle
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api.labs import taskqueue 
                
import logging
import random
import os
import Cookie
import re
import hashlib
import time
  
import settings
import models

import scapi

class RequestTokenHandler(webapp.RequestHandler):
  
  def get(self):
    callback_url = settings.APPLICATION_URL + "/soundcloud-connect/access-token/"
    oauth_authenticator = scapi.authentication.OAuthAuthenticator( \
                                               settings.OAUTH_CONSUMER_KEY,
                                               settings.OAUTH_CONSUMER_SECRET,
                                               None,
                                               None)                                                                                           
    connector = scapi.ApiConnector(host=settings.SOUNDCLOUD_API_URL, 
                                   authenticator=oauth_authenticator)      
    token, secret = connector.fetch_request_token( \
                    url = "http://api.soundcloud.com/oauth/request_token")
    logging.info("Token: " + token)
    logging.info("Secret: " +secret)        
    authorization_url = connector.get_request_token_authorization_url(token)
    logging.info("url" + authorization_url)
    
    url = authorization_url + "&oauth_callback=%s&display=popup" % callback_url
    logging.info("Redirect URL: " + url)  
    
    hash = hashlib.md5(repr(time.time()) + unicode(random.random())).hexdigest()
    
    oauthtoken = models.SoundCloudConnectUser(authorized = False,
                                              token = token,
                                              secret = secret,
                                              session_hash = hash)
    oauthtoken.put()
    
    c = Cookie.SimpleCookie()
    c["sid"] = hash
    c["sid"]["path"] = "/"
    logging.info(c.output())
    
    h = re.compile('^Set-Cookie: ').sub('', c.output(), count=1)
    self.response.headers.add_header('Set-Cookie', str(h))
    self.response.out.write("")      
    
    self.redirect(url)

    
class AccessTokenHandler(webapp.RequestHandler):
  
  def get(self):
    
    # TODO Test if Token and Secret provided match the saved ones from the cookie
    
    sid = self.request.cookies.get("sid")
    
    logging.info("SID: " + sid)
    
    user = models.SoundCloudConnectUser.all().filter('session_hash', sid).get()
    
    logging.info("user: " + str(user))
    
    token = user.token
    secret = user.secret
    auth = self.request.get('auth')
    
    oauth_authenticator = scapi.authentication.OAuthAuthenticator(settings.OAUTH_CONSUMER_KEY,
                                                                  settings.OAUTH_CONSUMER_SECRET,
                                                                  token,
                                                                  secret)  

    connector = scapi.ApiConnector(settings.SOUNDCLOUD_API_URL, authenticator=oauth_authenticator)
    token, secret = connector.fetch_access_token(auth)                                                                  
                            
    oauth_authenticator = scapi.authentication.OAuthAuthenticator( \
                                              settings.OAUTH_CONSUMER_KEY,
                                              settings.OAUTH_CONSUMER_SECRET,
                                              token,
                                              secret)         
    root = scapi.Scope(scapi.ApiConnector(host=settings.SOUNDCLOUD_API_URL,
                                          authenticator=oauth_authenticator))                                                                 
                                                                
    user.token = token
    user.secret = secret
    user.user_id = root.me().id
    user.authorized = True
    
    user.put()
    
    logging.info("you have been authet")
    logging.info("Token: " + token)
    logging.info("Secret: " + secret)
    
    # Lets get fill this backend up with the user-specific data
    
    # Create Followers task
    taskqueue.add(url='/backend/soundcloud-connect/followers/', 
                  params={'user_id': user.user_id})
    
    
    
def main():
  application = webapp.WSGIApplication([(r'/soundcloud-connect/request-token/', RequestTokenHandler),
                                        (r'/soundcloud-connect/access-token/', AccessTokenHandler)])
  run_wsgi_app(application)

if __name__ == '__main__':
  main()
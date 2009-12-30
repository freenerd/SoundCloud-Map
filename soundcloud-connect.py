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
                
import logging
import random
import os

import utils    
import settings
import models

import scapi

class MainHandler(webapp.RequestHandler):
  
  def get(self):
    self.response.out.write("TEST")    
    oauth_authenticator = scapi.authentication.OAuthAuthenticator(settings.OAUTH_CONSUMER_KEY,
                                                                  settings.OAUTH_CONSUMER_SECRET,
                                                                  None,
                                                                  None)
                                                                                                                              
    connector = scapi.ApiConnector(host=settings.SOUNDCLOUD_API_URL, authenticator=oauth_authenticator)  
    logging.info(dir(connector))  
    logging.info(connector.host)  
    logging.info(connector.authenticator)
    
    token, secret = connector.fetch_request_token("http://api.soundcloud.com/oauth/request_token")
    logging.info(token)
    logging.info(secret)        
    authorization_url = connector.get_request_token_authorization_url(token)
    logging.info(authorization_url)
    
    # oauth_verifier = raw_input("please enter verifier code as seen in the browser:")  
    
    
    # template_values = {
    #     'google_maps_api_key' : settings.GOOGLE_MAPS_API_KEY,
    #     'random' : random.random(),
    # }
    #     
    # path = os.path.join(os.path.dirname(__file__), 'templates/index.html')
    # self.response.out.write(template.render(path, template_values))
    self.response.out.write("TEST")    

def main():
  application = webapp.WSGIApplication([('.*', MainHandler)], debug=utils.in_development_enviroment())
  run_wsgi_app(application)

if __name__ == '__main__':
  main()
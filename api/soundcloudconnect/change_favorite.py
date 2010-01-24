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
import soundcloudconnect.utils

import scapi

class StatusHandler(webapp.RequestHandler):
  
  def get(self):
    
    # check if user is logged in
    session_hash = self.request.cookies.get("session_hash")
    if not session_hash:
      self.response.out.write("Not logged in")
      return
    
    soundcloudconnect_user = models.SoundCloudConnectUser.all().filter('session_hash', session_hash).get()
    root = soundcloudconnect.utils.get_api_root(soundcloudconnect_user)
    track_id = self.request.get("track-id")

    self.response.out.write("track_id") 
    self.response.out.write(track_id) 
    
    favs = list(root.me().favorites())
    
    self.response.out.write(str(favs))

class SetHandler(webapp.RequestHandler):
  
  def get(self):
    
    # check if user is logged in
    session_hash = self.request.cookies.get("session_hash")
    if not session_hash:
      self.response.out.write("Not logged in")
      return
    
    soundcloudconnect_user = models.SoundCloudConnectUser.all().filter('session_hash', session_hash).get()


class DeleteHandler(webapp.RequestHandler):
  
  def get(self):
    
    # check if user is logged in
    session_hash = self.request.cookies.get("session_hash")
    if not session_hash:
      self.response.out.write("Not logged in")
      return
    
    soundcloudconnect_user = models.SoundCloudConnectUser.all().filter('session_hash', session_hash).get()

      
    
    
def main():
  application = webapp.WSGIApplication([(r'/api/soundcloud-connect/change-favorite/status.*', StatusHandler),
                                        (r'/api/soundcloud-connect/change-favorite/set.*', SetHandler),
                                        (r'/api/soundcloud-connect/change-favorite/delete.*', DeleteHandler)])
  run_wsgi_app(application)

if __name__ == '__main__':
  main()
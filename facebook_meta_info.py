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

import util   
import settings
import models
   
class MainHandler(webapp.RequestHandler):
	
  def get(self):
    
    type = self.request.get('type')
    id = self.request.get('id')
    city = None
    track = None       
    if type and id:
      if type == 'track':
        track = models.Track.all().filter('track_id', int(id)).get()
        location = track.location.city
        title = 'Tracks On A Map: %s by %s' % (track.title, track.user.username)
      if type == 'city':
        city = models.Location.get_by_id(int(id))
        title = 'Tracks On A Map: %s in %s' % (city.city, city.country)     
    else:
      self.response.out.write('unknown')
      return

    template_values = {
        'title' : title,
        'city' : city,
        'track' : track
        'location': location
    }
    
    path = os.path.join(os.path.dirname(__file__), 'templates/facebook_meta_info.html')
    self.response.out.write(template.render(path, template_values))
                                                                        
def main():
  application = webapp.WSGIApplication([('.*', MainHandler)], debug=util.in_development_enviroment())
  run_wsgi_app(application)

if __name__ == '__main__':
  main()

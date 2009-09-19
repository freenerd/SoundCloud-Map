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

from google.appengine.api.labs import taskqueue
from google.appengine.ext import webapp   
from google.appengine.ext.webapp.util import run_wsgi_app

import logging
import time
import os

import models
import backend_utils 
import utils
    
class MainHandler(webapp.RequestHandler): 
	
	def get(self):
		"""
		Updating the Datastore with all the Track numbers per Location
		""" 
	
		id = int((self.request.uri).split('/')[-1])
		logging.error("Starting Updating Counter with id %i" % id)
	      
		time_start = time.time()
	
		while (time.time() - time_start) < 28:
			logging.error("Updating Counter for id %i at time %i" % (id, int((time.time() - time_start)))) 
			track = models.TrackCache.get_by_id(id)        
			
			if track:
				track_dict = { 'location_lng' : track.location_lng,
											 'location_lat' : track.location_lat,
												'city' : track.city,
												'country' : track.country}
				backend_utils.update_location_tracks_counter(track_dict)
			id += 1
		logging.error("done to id " + str(id))
		return "done to id " + str(id)
	                         
	
def main():
  application = webapp.WSGIApplication([('/backend-update-counter/', MainHandler),
																				('/backend-update-counter/.*', MainHandler),], debug=utils.in_development_enviroment())
  run_wsgi_app(application)	 
			
if __name__ == '__main__':
  main()
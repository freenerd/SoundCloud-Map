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

from google.appengine.runtime import DeadlineExceededError
from google.appengine.api import memcache
from google.appengine.ext import webapp

import wsgiref.handlers                
import logging
import time
import os

import models
import backend_utils

	
class FetchTrackInfo(webapp.RequestHandler):
	def post(self):
		"""
		This script queries the SoundCloud API, fetches the latest tracks having been uploaded
		since the last backend update, geocodes them and writes them to the database cache.
		It is intended to be called by a cronjob on a short basis, like every 3 minutes.
		"""

		try:  
			track_id = self.request.get('track_id')       
			track = memcache.get(track_id, namespace="backend_update_track")
			if track is None:
				logging.error("Fetching memcache item %s failed in backend track update" % track_id)  
				# return error code
					
			logging.info("Backend update started for track \"%s\" by \"%s\" (%s)." % \
									(track['title'], track['user']['username'], track['created_at']))
			
			if not track['streamable'] or track['sharing'] != 'public':
				logging.info("The track does not match our needs. Will not be used.")
				if memcache.delete(track_id, namespace="backend_update_track"):
					logging.error("Deletion from Memcache was not successfull.")
					# return error code
				# return 200

			# fetch complete user data
			userdata = open_soundcloud_api("/users/%s.json" % track['user']['permalink'])
			userdata = json.loads(userdata)
			track['user'] = userdata  

			# geolocate user
			# see if city / country already in database 
			try: 
				gecached_location = backend_utils.get_location(track['user']['city'], track['user']['country'])
			  
			 	location = models.Location( \
										location = gecached_location['location'],
										city = unicode(gecached_location['city']),
										country = unicode(gecached_location['country']),   
										track_counter = 1)
							
				#logging.info("Location for User \"%s\" is %s / %s." % (track['user']['username'], track['location_lat'], track['location_lng']))
				
				location.put()
				                  
			except RuntimeError:
				logging.info("No Location for User \"%s\" with City/Country: \"%s / %s\"." % \
										(track['user']['username'], track['user']['city'], track['user']['country']))
 				if memcache.delete(track_id, namespace="backend_update_track"):
					logging.error("Deletion from Memcache was not successfull.") 
				# return 200
				
			backend_utils.write_track_to_cache(track, location)
				
			if memcache.delete(track_id, namespace="backend_update_track"):
				logging.error("Deletion from Memcache was not successfull.")
			
								# tracks = backend_utils.remove_unusable_tracks(tracks)			
								# tracks = backend_utils.add_complete_user_data(tracks)
								# logging.info("Found %i new tracks" % len(tracks)) 
								# logging.info("Finished reading data from Soundcloud")
								# 
								# logging.info("Going to write %i new tracks to DB." % len(tracks)) 
								# counter_write = backend_utils.write_tracks_to_cache(tracks)
								# logging.info("Written %i new tracks to DB." % counter_write) 
								
		else:
			
			
			

       


			
		except DeadlineExceededError:
			logging.warning("Backend Update has been canceled due to Deadline Exceeded")
			for name in os.environ.keys():
				logging.info("%s = %s" % (name, os.environ[name]))		 
																																		 
def main():
  wsgiref.handlers.CGIHandler().run(webapp.WSGIApplication([
    ('/backend-update/track', FetchTrackInfo),
  ]))            
			
if __name__ == '__main__':
	main()
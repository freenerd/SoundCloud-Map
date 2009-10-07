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
import datetime

import models
import backend_utils 
import settings

	
class FetchTrackInfo(webapp.RequestHandler):
	
	def post(self):
		"""
		This script fetches the information for a track. It is meant to be called via TaskQueue.
		"""
     
		logging.info("Working the taskqueue. Fetching a new track.")
		
		try:                  
			# check, if track is not already overdue (which may happen, if memcache fails, which happens from time to time)
			if (self.request.get('time_track_added_to_queue') == '' or \
				 time.time() > (int(self.request.get('time_track_added_to_queue')) + settings.TRACK_BACKEND_UPDATE_LIFETIME * 60)):
				# track is overdue
				logging.info("Track with Track ID %s is overdue with time %s." % ((self.request.get('track_id') or ''), (self.request.get('time_track_added_to_queue') or ''))) 
				self.response.out.write("done") # finished processing script					
				return # return 200. task gets deleted from task queue					 
				
			# fetch track info from memcache
			track_id = self.request.get('track_id')
			track = memcache.get(track_id, namespace="backend_update_track")
			if track is None:
				logging.warning("Fetching memcache item %s failed in backend track update" % track_id)  
				self.response.set_status(500)
				return
					
			logging.info("Received the track \"%s\" by \"%s\" (id: %s, created at: %s)." % \
									(track['title'], track['user']['username'], track['id'], track['created_at']))
									
			# check if track meets our needs
			if not track['streamable'] or track['sharing'] != 'public':
				logging.info("The track does not match our needs. Will not be used.")
				if not memcache.delete(track_id, namespace="backend_update_track"):
					logging.error("Deletion from Memcache was not successfull.")
					self.response.set_status(500)
 				logging.info("End of track update, because track didn't fit our needs.")					
				self.response.out.write("done") # finished processing script        	
				return # return 200. task gets deleted from task queue

			# check if track is already in the datastore
			if models.Track.all().filter('track_id', int(track['id'])).get(): 
				logging.info("The track already is in the datastore.")
 				logging.info("End of track update, because the track is already in the datastore.")				
				self.response.out.write("done") # finished processing script        					
				return # return 200. task gets deleted from task queue
      
			# check if user is already in the datastore 		
			user = models.User.all().filter('user_id', int(track['user_id'])).get()
			if user:
				logging.info("User is already in datastore as permalink: %s user_id: %i" % (user.permalink, user.user_id))
				location = user.location																												
				backend_utils.update_location_data(track, location) 																									
			else:
 		 		# fetch complete user data
				logging.info("User is not in the datastore yet. Fetching user data.")
				track['user'] = backend_utils.open_remote_api("/users/%s.json" % track['user_id'], 'soundcloud') 
																								
				logging.info("User data fetched.")              
 				# determining location
		 		location = models.Location.all().filter('city', unicode(track['user']['city'])).filter('country', unicode(track['user']['country'])).get()
				if location:
						logging.info("Location is already in datastore: city: %s country: %s lat / lon: %s / %s" % \
												(track['user']['city'], track['user']['country'], location.location.lat, location.location.lon)) 
						backend_utils.update_location_data(track, location)						
				else:
					try:
						if track['user']['city'] == None or track['user']['country'] == None:
							raise RuntimeError
						logging.info("Looks as if location is not in the datastore yet. Fetching it ...")
						gecached_location = backend_utils.get_location(track['user']['city'], track['user']['country'])	
						# check again, if location not in datastore already
						location = models.Location.all().filter('location', gecached_location['location']).get()
						if location:    
							logging.info("Location has yet already been in datastore. Updating it.") 
							backend_utils.update_location_data(track, location)                                                                                                                                           
						else:
					 	 	location = models.Location( \
													location = gecached_location['location'],
													city = unicode(gecached_location['city']),
													country = unicode(gecached_location['country']),   
													track_counter = 1,
													last_time_updated=datetime.datetime.now()) 								
							logging.info("Saving new location for user \"%s\" lat/lon %s/%s in city/country %s/%s to datastore ..." % \
													(track['user']['username'], location.location.lat, location.location.lon, location.city, location.country))
							location.put()
						 	backend_utils.update_location_genre_data(track, location)
							logging.info("New location saved to datastore.") 
		                  
					except RuntimeError:
						logging.info("No Location for User \"%s\" with City/Country: \"%s / %s\"." % \
												(track['user']['username'], track['user']['city'], track['user']['country']))
		 				if not memcache.delete(track_id, namespace="backend_update_track"):
							logging.error("Deletion from Memcache was not successful.") 
							self.response.set_status(500)
 						logging.info("End of track update because could not be geolocated.")							
						self.response.out.write("done") # finished processing script        	
						return # return 200. task gets deleted from task queue
				
				logging.info("Saving user data (id: %s, permalink: %s) to datastore ..." % (track['user']['id'], track['user']['permalink']))
 				user = models.User( \
									user_id = track['user']['id'],
									permalink = track['user']['permalink'],
									permalink_url = track['user']['permalink_url'],
									username = track['user']['username'],
									fullname = track['user']['full_name'],
									avatar_url = track['user']['avatar_url'],
									location = location.key())	         
				user.put()
				logging.info("User saved to datastore.")     

			backend_utils.write_track_to_datastore(track, user, location)
				
			if not memcache.delete(track_id, namespace="backend_update_track"):
				logging.error("Deletion from Memcache was not successful.")
				self.response.set_status(500)
				self.response.out.write("done")
				return

			logging.info("End of track update.") 			
			self.response.set_status(200)
			self.response.out.write("done") # finished processing script
			return # return 200. task gets deleted from task queue 
	
		except DeadlineExceededError:
			logging.warning("Backend Update for track id: %s has been canceled due to Deadline Exceeded" % track_id)
			for name in os.environ.keys():
				logging.info("%s = %s" % (name, os.environ[name]))
			self.response.set_status(500)
			return			 
																																		 
def main():
  wsgiref.handlers.CGIHandler().run(webapp.WSGIApplication([
    ('/backend-update/track', FetchTrackInfo),
  ]))            
			
if __name__ == '__main__':
	main()
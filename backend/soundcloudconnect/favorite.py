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
from google.appengine.api.labs import taskqueue 
from google.appengine.api import memcache
from google.appengine.ext import webapp 
from google.appengine.ext.webapp.util import run_wsgi_app

import wsgiref.handlers     
import logging
import time

import settings
import models
import util
import backend.utils
import soundcloudconnect.utils

def fetch_favorite(self):
  logging.info("Working the taskqueue. Fetching a new favorite")                            
         
  # check, if favorite is not already overdue (which may happen, if memcache fails, which happens from time to time)
  # if (self.request.get('time_favorite_added_to_queue') == '' or \
  #    time.time() > (int(self.request.get('time_favorite_added_to_queue')) + settings.TRACK_BACKEND_UPDATE_LIFETIME * 60)):
  #   # favorite is overdue
  #   logging.info("Track with Track ID %s is overdue with time %s." % ((self.request.get('favorite_id') or ''), (self.request.get('time_favorite_added_to_queue') or ''))) 
  #   self.response.out.write("done") # finished processing script          
  #   return # return 200. task gets deleted from task queue      
  
  # fetch favorite info from memcache
  
  memcache_namespace = 'soundcloudconnect_favorites'
  
  if not (self.request.get('session_hash') and
          self.request.get('favorite_id')):
    logging.error('Error in taskqueue. Problem with parameters. session_hash: %s Track_ID: %s' % (self.request.get('session_hash'), self.request.get('favorite_id')))
    return          
  
  session_hash = self.request.get('session_hash')
  soundcloudconnect_user = models.SoundCloudConnectUser.all().filter('session_hash', session_hash).get()
  if not soundcloudconnect_user:
    logging.error('Error in taskqueue. Problem with soundcloudconnect_user. session_hash: %s soundcloudconnect_user: %s' % (self.request.get('session_hash'), soundcloudconnect_user))
    return
  
  favorite_id = self.request.get('favorite_id')
  favorite = memcache.get(favorite_id, namespace=memcache_namespace)
  logging.info("Track" + str(favorite))
  if favorite is None:
    logging.warning("Fetching memcache item %s failed in soundcloud-connect fetch favorite" % person_id)  
    self.response.set_status(500)
    return
    
  if not backend.utils.check_if_track_meets_our_needs(favorite):
    logging.info("Track does not meet our needs. Is dropped")
    return
  
  # check if track is already in database  
  track = models.Track.all().filter('track_id', int(favorite_id)).get()
  if track:
    logging.info("Track already is in the database")
    location = track.location
  else:    
    logging.info("Track is not in the Datastore yet. Fetching new Info.")
    
    user = None    
    # fetch user info
    root = soundcloudconnect.utils.get_api_root(soundcloudconnect_user)
    user = root.User.get(favorite['user_id'])._RESTBase__data
    if not user:
      logging.error("We have no user for this track? Something went terribly wrong!")
      return
        
    try:
      location = backend.utils.wrapped_get_location(user['city'],
                                                    user['country'],
                                                    favorite)
      logging.info(location)
                                                      
      if not location:
        # if not memcache.delete(track_id, namespace="backend_update_track"):
        #   logging.error("Deletion from Memcache was not successful.") 
        #   self.response.set_status(500)
        #   logging.info("End of track update because could not be geolocated.")  
        # self.response.out.write("done") # finished processing script          
        return # return 200. task gets deleted from task queue   
      
    except RuntimeError:
      logging.info("Runtime Error in GeoLocating")
      return

    # writing user and favorite to database
    user = backend.utils.write_user_to_datastore(user, location)
    logging.info(str(favorite))
    track = backend.utils.write_track_to_datastore(favorite, user, location)
    logging.info("Written user and track to datastore.")
    logging.info("Track: %s" % str(track))    
    logging.info("User: %s" % str(user))        
    
  # Update SoundCloudConnectUser Record  
  soundcloudconnect_user.geolocated_favorites += 1  
    
  # Update SoundCloudConnectUserLocation Record
  soundcloudconnect_user_location = models.SoundCloudConnectUserLocation.all()
  soundcloudconnect_user_location = soundcloudconnect_user_location.filter('soundcloudconnect_user', soundcloudconnect_user)
  soundcloudconnect_user_location = soundcloudconnect_user_location.filter('location', location).get()

  if soundcloudconnect_user_location:
    soundcloudconnect_user_location.favorite_count += 1
    if soundcloudconnect_user.max_location_favorites_count < \
       soundcloudconnect_user_location.favorite_count:
       soundcloudconnect_user.max_location_favorites_count = \
            soundcloudconnect_user_location.favorite_count
  else:
    favorite_count = 1
    if soundcloudconnect_user.max_location_favorites_count < 1:
       soundcloudconnect_user.max_location_favorites_count = 1  
    soundcloudconnect_user_location = models.SoundCloudConnectUserLocation(\
                                              follower_count = 0,
                                              following_count = 0,
                                              favorite_count = favorite_count,
                                              soundcloudconnect_user = soundcloudconnect_user,
                                              location = location)
  
  soundcloudconnect_user_location.put()  
  soundcloudconnect_user.put()
    
  # Update SoundCloudConnectFavorite Record
  soundcloudconnect_favorite = models.SoundCloudConnectFavorite(\
                                          soundcloudconnect_user = soundcloudconnect_user,
                                          track = track,
                                          location = location)  
  soundcloudconnect_favorite.put()
  
  logging.info("This is the end")  
  return 
  
class Favorite(webapp.RequestHandler):
  def get(self):
    return fetch_favorite(self)
  def post(self):
    return fetch_favorite(self)
      
def main():
  application = webapp.WSGIApplication([\
                      ('/backend/soundcloud-connect/favorite/', Favorite),
                      ], debug=util.in_development_enviroment())
  run_wsgi_app(application)            
      
if __name__ == '__main__':
  main()    

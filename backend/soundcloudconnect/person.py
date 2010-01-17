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

import wsgiref.handlers     
import logging
import time

import settings
import models
import backend.utils
import soundcloudconnect.utils

def fetch_person(self, type=''):
  logging.info("Working the taskqueue. Fetching a new " + type)                            
         
  # check, if track is not already overdue (which may happen, if memcache fails, which happens from time to time)
  # if (self.request.get('time_track_added_to_queue') == '' or \
  #    time.time() > (int(self.request.get('time_track_added_to_queue')) + settings.TRACK_BACKEND_UPDATE_LIFETIME * 60)):
  #   # track is overdue
  #   logging.info("Track with Track ID %s is overdue with time %s." % ((self.request.get('track_id') or ''), (self.request.get('time_track_added_to_queue') or ''))) 
  #   self.response.out.write("done") # finished processing script          
  #   return # return 200. task gets deleted from task queue      
  
  # fetch person info from memcache
  
  if type == 'follower':
    memcache_namespace = 'soundcloudconnect_follower'
  elif type == 'following':
    memcache_namespace = 'soundcloudconnect_following'
  else:
    self.response.out.write('ERROR')
    return
  
  if not (self.request.get('soundcloudconnect_user_id') and
          self.request.get('person_id')):
    logging.error('Error in taskqueue. Problem with parameters. SoundcloudConnect_following: %s Person_ID: %s' % (self.request.get('soundcloudconnect_user_id'), self.request.get('person_id')))
    return          
  
  soundcloudconnect_user_id = int(self.request.get('soundcloudconnect_user_id'))
  
  person_id = self.request.get('person_id')
  person = memcache.get(person_id, namespace=memcache_namespace)
  logging.info("Person" + str(person))
  if person is None:
    logging.warning("Fetching memcache item %s failed in soundcloud-connect fetch person" % person_id)  
    self.response.set_status(500)
    return 
  
  # check if user is already in database  
  user = models.User.all().filter('user_id', person_id).get()
  if user:
    logging.info("User already is in the database")
  else:    
    logging.info("User is not in the Datastore yet. Fetching new Info.")
    
    # fetch track info
    if person['track_count'] != 0:
      root = soundcloudconnect.utils.get_api_root(soundcloudconnect_user_id)
      tracks = list(root.User.get(person['id']).tracks())
      if tracks:
        for track in tracks:
          if backend.utils.check_if_tracks_meets_our_needs(track)
            logging.info("We have a track for this user: " + str(track))
            break
        else:
    if not track:
      track = None
      logging.info("We have no track for this user.")        
        
    try:
      location = backend.utils.wrapped_get_location(person['city'],
                                                    person['country'],
                                                    track)
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

    # everything went fine ... 
    user = backend.utils.write_user_to_datastore(person, location)
    
  # Update SoundCloudConnectUser Record  
  soundcloudconnect_user = models.SoundCloudConnectUser.all().filter('session_hash', soundcloudconnect_user_id).get()
  if type == 'follower':
    soundcloudconnect_user.geolocated_followers += 1
  elif type == 'following':
    soundcloudconnect_user.geolocated_followings += 1  
  soundcloudconnect_user.put()    
    
  # Update SoundCloudConnectUserLocation Record
  soundcloudconnect_user_location = models.SoundCloudConnectUserLocations.all().filter('location', location).get()
  if soundcloudconnect_user_location:
    if type == 'follower': soundcloudconnect_user_location.follower_count += 1
    elif type == 'following': soundcloudconnect_user_location.following_count += 1  
  else:
    if type == 'follower': 
      follower_count = 1
      following_count = 0
    elif type == 'following':
      follower_count = 1
      following_count = 0
    soundcloudconnect_user_location = models.SoundCloudConnectUserLocations(\
                                              follower_count = follower_count,
                                              following_count = following_count,
                                              favorite_count = 0,
                                              soundcloudconnect_user = soundcloudconnect_user,
                                              location = location)
    soundcloudconnect_user_location.put()  
    
  # Update SoundCloudConnectFollower/Following Record
  if type == 'follower': 
    soundcloudconnect_follower = models.SoundCloudConnectFollower.all().filter('location', location).get()
    if soundcloudconnect_follower:
      soundcloudconnect_follower.follower_count += 1
    else:
      soundcloudconnect_follower = models.SoundCloudConnectFollower(\
                                              soundcloudconnect_user = soundcloudconnect_user,
                                              follower = user,
                                              location = location)  
      soundcloudconnect_follower.put()
  elif type == 'following':
    soundcloudconnect_following = models.SoundCloudConnectFollowing.all().filter('location', location).get()
    if soundcloudconnect_following:
      soundcloudconnect_following.following_count += 1
    else:
      soundcloudconnect_following = models.SoundCloudConnectFollower(\
                                              soundcloudconnect_user = soundcloudconnect_user,
                                              following = user,
                                              location = location)   
      soundcloudconnect_following.put()

  # check if track is already in the datastore
  if models.Track.all().filter('track_id', int(track['id'])).get(): 
    logging.info("The track already is in the datastore.")
  else:
    write_track_to_datastore(track, user, location):
  
  logging.info("This is the end")  
  self.response.set_status(500)
  return
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
from google.appengine.ext import webapp 

import wsgiref.handlers                
import logging
import time
import os
import datetime
import hashlib

from api.utils import error_response
import models
import backend.utils 
import settings

  
class FetchTrackInfo(webapp.RequestHandler):
  
  def post(self):
    """
    This script fetches the information for a track. It is meant to be called via TaskQueue.
    """
     
    logging.info("Working the taskqueue. Fetching a new track.")
    
    try:                  
      # check, if track is not already overdue
      if (self.request.get('time_track_added_to_queue') == '' or \
         time.time() > (int(self.request.get('time_track_added_to_queue')) + settings.TRACK_BACKEND_UPDATE_LIFETIME * 60)):
        # track is overdue
        logging.error("Track with Track ID %s is overdue with time %s." % ((self.request.get('track_id') or ''), (self.request.get('time_track_added_to_queue') or ''))) 
        self.response.out.write("done") # finished processing script          
        return # return 200. task gets deleted from task queue           
        
      # get all the other data from the POST request
      track_id = self.request.get('track_id', None)
      city = self.request.get('city', None)
      country = self.request.get('country', None)
      twitter_name = self.request.get('twitter_name', None)      
      twitter_url = self.request.get('twitter_url', None)  

      # fetch track info from soundcloud
      query = "/tracks/%s.json" % track_id
      track = backend.utils.open_remote_api(query, "soundcloud")

      if track.get('error', False):
        logging.warning("Fetching track failed in backend track update")  
        error_response(self, 
                       "TrackNotFound",
                       "SoundCloud does not have track with id %s" % track_id)
        return
          
      logging.info("Received the track \"%s\" by \"%s\" (id: %s, created at: %s)." % \
                  (track['title'], track['user']['username'], track['id'], track['created_at']))
                  
      # check if track meets our needs
      if not backend.utils.check_if_track_meets_our_needs(track):
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
        backend.utils.update_location_data(track, location)                                                   
      else:
        # fetch complete user data
        logging.info("User is not in the datastore yet. Fetching user data.")
        track['user'] = backend.utils.open_remote_api("/users/%s.json" % track['user_id'], 'soundcloud') 
        logging.info("User data fetched.")              
        
        # determining location
        location = backend.utils.wrapped_get_location( \
                                          city,
                                          country,
                                          track)
        if not location:
          logging.info("End of track update because could not be geolocated.")  
          self.response.out.write("done") # finished processing script          
          return # return 200. task gets deleted from task queue                                                     
        
        # apparently has been geolocated fine so lets continue ...
        track['user']['twitter_name'] = twitter_name
        track['user']['twitter_url'] = twitter_url
        user = backend.utils.write_user_to_datastore(track['user'], location)

      backend.utils.write_track_to_datastore(track, user, location)
      
      # notify twestival.fm of the saved track
      md5base = str(track['id'])
      md5base += twitter_name
      md5base += settings.TWESTIVAL_FM_TWITTER_SALT
      md5digest = hashlib.md5(md5base).hexdigest()
      
      logging.info("Adding Make Tweet to taskqueue")        
      taskqueue.add(url='/backend/put-my-track-on-a-map/make-tweet', 
                    params={'track_id': str(track['id']), 
                            'twitter_name': twitter_name,
                            'hash': md5digest,
                            'time_added_to_queue': str(int(time.time()))})
            
      logging.info("End of track update.")      
      self.response.set_status(200)
      self.response.out.write("done") # finished processing script
      return # return 200. task gets deleted from task queue 
  
    except DeadlineExceededError:
      logging.warning("Backend Update for track id: %s has been canceled due to Deadline Exceeded" % track_id)
      for name in os.environ.keys():
        logging.info("%s = %s" % (name, os.environ[name]))
      self.response.set_SoundCloudConnectUserLocation
      return       
                                                                     
def main():
  wsgiref.handlers.CGIHandler().run(webapp.WSGIApplication([
    ('/backend/put-my-track-on-a-map/work', FetchTrackInfo),
  ]))            
      
if __name__ == '__main__':
  main()
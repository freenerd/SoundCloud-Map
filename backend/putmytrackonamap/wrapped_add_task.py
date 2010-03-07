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
import os

import models
import backend.utils 
import settings
from api.utils import error_response

class PutMyTrackOnAMap(webapp.RequestHandler):
  
  def post(self):
    """
    Take a track-id and some more information and queue it up.
    """
    try:
      logging.info("Backend put my track on a map started")

      logging.info(self.request.get_all)    
      track_id = self.request.get('trackid')

      
      # TODO: check if already in database and return that if true
      
      query = "/tracks/%s.json" % track_id
      try:
        track = backend.utils.open_remote_api(query, "soundcloud") 
        logging.info(track)
      except ValueError:
        error_response(self, 
                       "TrackNotFound",
                       "SoundCloud is behaving strange")
        return
        
      if track.get('error', False):
        error_response(self, 
                       "TrackNotFound",
                       "SoundCloud does not have track with id %s" % track_id)
        return
      else:
        logging.info("adding to memcache and taskqueue")        
        memcache_add = memcache.add(track_id, 
                                    track,
                                    time=settings.TRACK_BACKEND_UPDATE_LIFETIME*60, 
                                    namespace="put_my_track_on_a_map")
        if memcache_add: 
          taskqueue.add(url='/backend/put-my-track-on-a-map/work', 
                        params={'track_id': track_id, 
                                'time_track_added_to_queue': str(int(time.time()))})
          logging.info("Added track_id %s to memcache and task queue." % track['id'])
        self.response.out.write("done")
          
          
      
        
      
    

    
      # get more data
      # 
      # get that track from soundcloud 
      # 
      # if cool
      # 
      #   put it in the queue
      #   return success
      # if wrong
      #   return failure


          # 
          # logging.info("Fetching the tracks from SoundCloud")
          # time_from = self.request.get('time_from')
          # time_to = self.request.get('time_to')   
          # tracks = backend.utils.get_latest_tracks_from_soundcloud()
          # logging.info("Fetched %i tracks from Soundcloud" % len(tracks)) 
          # if len(tracks) > 0:
          #   counter = 0    
          #   for track in tracks:
          #     track['id'] = unicode(track['id'])
          #     memcache_add = memcache.add(track['id'], 
          #                                 track,
          #                                 time=settings.TRACK_BACKEND_UPDATE_LIFETIME*60, 
          #                                 namespace="backend_update_track")
          #     if memcache_add: 
          #       taskqueue.add(url='/backend-update/track', 
          #                     params={'track_id': track['id'], 
          #                             'time_track_added_to_queue': str(int(time.time()))})
          #       logging.info("Added track_id %s to memcache and task queue." % track['id'])
          #       counter += 1          
          #     else:
          #       logging.error("Setting Memcache failed for track \"%s\" by \"%s\" (id: %s, created at: %s)." % \
          #                   (track['title'], track['user']['username'], track['id'], track['created_at']))
          #   logging.info("Added %i tracks to the taskqueue" % counter)
          # else:
          #   logging.info("Backend update finished without new tracks") 
    
    except DeadlineExceededError:
      logging.warning("Backend Update has been canceled due to Deadline Exceeded")
      for name in os.environ.keys():
        logging.info("%s = %s" % (name, os.environ[name]))

def main():
  wsgiref.handlers.CGIHandler().run(webapp.WSGIApplication([
    (r'/backend/put-my-track-on-a-map', PutMyTrackOnAMap),
  ]))            
      
if __name__ == '__main__':
  main()
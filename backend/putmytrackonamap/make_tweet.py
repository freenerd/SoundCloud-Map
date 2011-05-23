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
from google.appengine.api import urlfetch
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

  
class MakeTweetHandler(webapp.RequestHandler):
  
  def post(self):
    """
    This script calls twestival-fm to send a tweet. It is meant to be called via TaskQueue.
    """
     
    logging.info("Working the taskqueue. Trying to make a tweet.")
    
    try:                       
      # get all the other data from the POST request
      track_id = self.request.get('track_id', None)
      twitter_name = self.request.get('twitter_name', None)      
      hash = self.request.get('hash', None)  
      
      # check, if tweet is not already overdue
      if (self.request.get('time_added_to_queue') == '' or \
         time.time() > (int(self.request.get('time_added_to_queue')) + settings.TRACK_BACKEND_UPDATE_LIFETIME * 60)):
        logging.error("Tweet for user %s is overdue with time %s." % ((self.request.get('twitter_name') or ''), (self.request.get('time_added_to_queue') or ''))) 
        self.response.out.write("done") # finished processing script          
        return # return 200. task gets deleted from task queue      
      
      # fetch track info from soundcloud
      query = settings.TWESTIVAL_FM_MAKE_TWEET_URL
      query += "?track_id=" + track_id
      query += "&twitter_name=" + twitter_name
      query += "&hash=" + hash
      
      logging.info("Trying to query: %s" % query)
      result = urlfetch.fetch(query, deadline=10)

      self.response.set_status(result.status_code)
      logging.info("Finished query with status code %i" % result.status_code)
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
    ('/backend/put-my-track-on-a-map/make-tweet', MakeTweetHandler),
  ]))            
      
if __name__ == '__main__':
  main()
#!/usr/bin/env python

# Copyright (c) 2009 Johan Uhle
# 
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# 'Software'), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
# 
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND,
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

import logging
import time

import settings
import models
import util
from soundcloudconnect import utils


def fetch_favorites(self):
  '''
    Fetching favorites information for a soundcloud-connect user
    and putting single fetch task into the taskqeue ...
  '''
  
  session_hash = self.request.get('session_hash')
  logging.info('SessionHash: ' + session_hash)
  soundcloudconnect_user = models.SoundCloudConnectUser.all().filter('session_hash', session_hash).get()
  logging.info('scconnectuser_data: ' + str(soundcloudconnect_user))
  
  # TODO: Fetch with offset to get more than 50 favorites
  
  root = utils.get_api_root(soundcloudconnect_user)
  
  favorites = list(root.me().favorites())
  memcache_namespace = 'soundcloudconnect_favorites'
  taskqueue_url = '/backend/soundcloud-connect/favorite/'    
  
  #logging.info("Favorites:" + str(favorites))
  
  for favorite in favorites:
    logging.info("Favorite str:" + str(favorite))
    logging.info("Favourite dict:" + str(favorite.__dict__))
    favorite_id = unicode(favorite._RESTBase__data['id'])
    memcache_add = memcache.add(favorite_id, 
                                favorite._RESTBase__data,
                                time=settings.TRACK_BACKEND_UPDATE_LIFETIME*60, 
                                namespace=memcache_namespace)
                                
    if memcache_add: 
      taskqueue_add = taskqueue.add(url=taskqueue_url, 
                                    params={'favorite_id': favorite_id, 
                                            'session_hash': session_hash,
                                            'time_added_to_queue': \
                                                      str(int(time.time()))})
      if taskqueue_add:                                              
        logging.info('Added to queue')      
      else:
        logging.error('Error adding to taskqueue for ' + str(favorite_id))
    else:
      logging.error('Error adding to memcache for ' + str(favorite_id))     
  
  # TODO: Update stat counters for soundcloud connect user
         
  logging.info('Finished fetching network')
  return                        
  

class Favorites(webapp.RequestHandler):
  def get(self):
    return fetch_favorites(self)
  def post(self):
    return fetch_favorites(self)
      
def main():
  application = webapp.WSGIApplication([\
                      ('/backend/soundcloud-connect/favorites/', Favorites),
                      ], debug=util.in_development_enviroment())
  run_wsgi_app(application)            
      
if __name__ == '__main__':
  main()  
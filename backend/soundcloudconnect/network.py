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


def fetch_network(self, type=''):
  '''
    Fetching network information for a soundcloud-connect user
    and putting single fetch task into the taskqeue ...
    This method is not intendend to be used directly but is
    getting called either by followers.py or followings.py
  '''
  
  session_hash = self.request.get('session_hash')
  logging.info('SessionHash: ' + session_hash)
  soundcloudconnect_user = models.SoundCloudConnectUser.all().filter('session_hash', session_hash).get()
  logging.info('scconnectuser_data: ' + str(soundcloudconnect_user))
  
  # TODO: Fetch with offset to get more than 50 people
  
  root = utils.get_api_root(soundcloudconnect_user)
  
  if type == 'followers':
    network = list(root.me().followers())
    memcache_namespace = 'soundcloudconnect_follower'
    taskqueue_url = '/backend/soundcloud-connect/follower/'
  elif type == 'followings':
    network = list(root.me().followings())
    memcache_namespace = 'soundcloudconnect_following'
    taskqueue_url = '/backend/soundcloud-connect/following/'    
  else:
    self.response.out.write('ERROR')
    return
  
  for person in network:
    logging.info(person)
    person_id = unicode(person['id'])
    memcache_add = memcache.add(person_id, 
                                person,
                                time=settings.TRACK_BACKEND_UPDATE_LIFETIME*60, 
                                namespace=memcache_namespace)
                                
    if memcache_add: 
      taskqueue.add(url=taskqueue_url, 
                    params={'person_id': person_id, 
                            'session_hash': session_hash,
                            'time_follower_added_to_queue': str(int(time.time()))})
      logging.info('Added to queue')      
    else:
      logging.error('Error adding to network queue for ' + type)     
  
  # TODO: Update stat counters for soundcloud connect user
         
  logging.info('Finished fetching network')
  return                        
  

class Followers(webapp.RequestHandler):
  def get(self):
    return fetch_network(self,'followers')    
  def post(self):
    return fetch_network(self,'followers')    
  
class Followings(webapp.RequestHandler):
  def get(self):
    return fetch_network(self,'followings')
  def post(self):
    return fetch_network(self,'followings')
      
def main():
  application = webapp.WSGIApplication([\
                      ('/backend/soundcloud-connect/followers/', Followers),
                      ('/backend/soundcloud-connect/followings/', Followings)    
                      ], debug=util.in_development_enviroment())
  run_wsgi_app(application)            
      
if __name__ == '__main__':
  main()  
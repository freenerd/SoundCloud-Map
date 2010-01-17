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

import wsgiref.handlers     
import logging
import time

import settings
import models
from soundcloudconnect import utils


def fetch_network(self, type=''):
  '''
    Fetching network information for a soundcloud-connect user
    and putting single fetch task into the taskqeue ...
    This method is not intendend to be used directly but is
    getting called either by followers.py or followings.py
  '''
  
  sid = self.request.cookies.get('sid')
  logging.info('SID: ' + sid)
  sid_data = models.SoundCloudConnectUser.all().filter('session_hash', sid).get()
  logging.info('sid_data: ' + str(sid_data))
  user_id = sid_data.user_id
  
  root = utils.get_api_root(int(user_id))
  
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
  
  for person in network[0:5]:
    logging.info(person)
    person_id = unicode(person['id'])
    memcache_add = memcache.add(person_id, 
                                person,
                                time=settings.TRACK_BACKEND_UPDATE_LIFETIME*60, 
                                namespace=memcache_namespace)
                                
    if memcache_add: 
      taskqueue.add(url=taskqueue_url, 
                    params={'person_id': person_id, 
                            'soundcloudconnect_user_id': user_id,
                            'time_follower_added_to_queue': str(int(time.time()))})
      logging.info('Added to queue')      
    else:
      logging.error('Error adding to network queue for ' + type)     
  
  # TODO: Update stat counters for soundcloud connect user
         
  logging.info('Finished fetching network')
  return                        
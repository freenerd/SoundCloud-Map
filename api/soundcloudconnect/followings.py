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

from google.appengine.ext import webapp

import logging

import models
import scapi
import settings

import backend.utils
import api.utils

class SoundCloudConnectFollowingsHandler(webapp.RequestHandler):
  def get(self):
    
    # memcached = memcache.get(self.request.path_qs, namespace='api_cache' )
    # if memcached is not None and not utils.in_development_enviroment():
    #   return self.response.out.write(memcached)    
    
    # check if user is logged in
    session_hash = self.request.cookies.get("session_hash")
    if not session_hash:
      self.response.out.write("Not logged in")
      return
    
    soundcloudconnect_user = models.SoundCloudConnectUser.all().filter('session_hash', session_hash).get()
    
    locations = models.SoundCloudConnectUserLocations.all()
    locations = locations.filter('soundcloudconnect_user',  soundcloudconnect_user)
    locations = locations.filter('following_count >', 0)
    
    logging.info("Fetched Locations: " + str(locations))
    
    locations_array = []
    
    for location in locations:
      logging.info("Caring for location: " + "")
      location_dict = api.utils.create_location_dict(location.location, location.following_count)
      locations_array.append(location_dict)
    
    api.utils.memcache_and_output_array(self, locations_array, memcache_name_suffix=str(soundcloudconnect_user.user_id))
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

class FavoritesHandler(webapp.RequestHandler):
  def get(self):
    
    # memcached = memcache.get(self.request.path_qs, namespace='api_cache' )
    # if memcached is not None and not utils.in_development_enviroment():
    #   return self.response.out.write(memcached)    
    
    # initialization
    genre = self.request.get('genre')   
    if self.request.get('limit'):
      limit = int(self.request.get('limit'))
    else:
      limit = settings.FRONTEND_LOCATIONS_LIMIT
    if self.request.get('offset'):
      offset = int(self.request.get('offset'))
    else:
      offset = 0    
    
    # check if user is logged in
    session_hash = self.request.cookies.get("session_hash")
    if not session_hash:
      self.response.out.write("Not logged in")
      return
    
    soundcloudconnect_user = models.SoundCloudConnectUser.all().filter('session_hash', session_hash).get()
    
    favorites = models.SoundCloudConnectUserLocations.all()
    favorites = locations.filter('soundcloudconnect_user',  soundcloudconnect_user)
    favorites = locations.filter('favorites_count >', 0)
    favorites = locations.fetch(limit, offset)
    
    logging.info("Fetched Locations: " + str(locations))
    
    locations_array = []
    
    for location in locations:
      logging.info("Caring for location: " + "")
      location_dict = api.utils.create_location_dict(location.location, location.following_count)
      locations_array.append(location_dict)
    
    api.utils.memcache_and_output_array(self, locations_array, memcache_name_suffix=str(soundcloudconnect_user.user_id))

class TracksInLocationHandler(webapp.RequestHandler):
  def get(self):
    
    location_id = self.request.get('location')
    
    if not location_id:
      api.utils.error_response(self, 'no location_id', 'please specify the location_id like .../tracks-in-location/1234')
      return
    
    location = models.Location.get_by_id(int(location_id))
    
    if not location:
      api.utils.error_response(self, 'location not found', 'the location has not been found', 404)
      return
    
    # memcached = memcache.get(self.request.path_qs, namespace='api_cache' )
    # if memcached is not None and not utils.in_development_enviroment():
    #   return self.response.out.write(memcached)    
    
    # initialization
    # genre = self.request.get('genre')   
    if self.request.get('limit'):
      limit = int(self.request.get('limit'))
    else:
      limit = settings.FRONTEND_LOCATIONS_LIMIT
    if self.request.get('offset'):
      offset = int(self.request.get('offset'))
    else:
      offset = 0    
    
    # check if user is logged in
    session_hash = self.request.cookies.get("session_hash")
    if not session_hash:
      self.response.out.write("Not logged in")
      return
    
    soundcloudconnect_user = models.SoundCloudConnectUser.all().filter('session_hash', session_hash).get()
    
    # get favorites
    favorites = models.SoundCloudConnectFavorites.all()
    favorites = followers.filter('soundcloudconnect_user',  soundcloudconnect_user)
    favorites = followers.filter('location', location)
    favorites = followers.fetch(limit, offset)
    
    logging.info(favorites)
    logging.info(len(favorites))        
    
    track_array = []
    
    for track in favorites:
      logging.info("TRACK" + str(track))
      api.utils.add_to_track_array(track, track_array)

    api.utils.memcache_and_output_array(self, track_array, memcache_name_suffix=str(soundcloudconnect_user.user_id))    
    
class MaxFavoritesHandler(webapp.RequestHandler):
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
    
    api.utils.memcache_and_output_array(self, 
                                        {'max_tracks': soundcloudconnect_user.max_location_favorites_count}, 
                                        memcache_name_suffix=str(soundcloudconnect_user.user_id))    
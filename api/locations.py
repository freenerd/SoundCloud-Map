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
from google.appengine.api import memcache

import util
import settings
import models
from api import utils

def fetch_location_by_id(self, location_id): 
  """
    Return location_array with only one location for location_id
  """
  locations_array = []
  location = models.Location.get_by_id(int(location_id))
  if location:
    locations_array.append(create_location_dict(location))
    return utils.memcache_and_output_array(self, locations_array)
  else:
    utils.error_response(self, 'location_not_found', 'The location with the location_id %s is not in the datastore.' % location_id)
  return

class MaxTracksHandler(webapp.RequestHandler):
  """
    Fetch the biggest track_counter of the latest-updated locations. Returning json
  """
  def get(self):

    memcached = memcache.get(self.request.path_qs, namespace='api_cache' )
    if memcached is not None and not util.in_development_enviroment():
      return self.response.out.write(memcached)

    # initialization
    locations_array = []
    genre = self.request.get('genre')   
    if self.request.get('limit'):
      limit = int(self.request.get('limit'))
    else:
      limit = settings.FRONTEND_LOCATIONS_LIMIT
    if self.request.get('offset'):
      offset = int(self.request.get('offset'))
    else:
      offset = 0

    # Processing latest locations for a certain genre api/locations/?genre={genre_name}
    if genre and genre != 'all':
      if genre not in utils.genres:
        error_response(self, 'unknown_genre', 'Sorry, but we do not know the genre %s.' % genre) 
        return
      location_genres = models.LocationGenreLastUpdate.all().order('-last_time_updated').filter('genre', genre).fetch(limit, offset)
      if location_genres:
        max_tracks = 0
        for location_genre in location_genres:
          if location_genre.track_counter > max_tracks:
            max_tracks = location_genre.track_counter
        return utils.memcache_and_output_array(self, {'max_tracks': max_tracks}, (settings.MAX_TRACKS_CACHE_TIME-5))
      else:
        self.response.out.write("[]") # empty array
      return
    
    # Processing latest locations for api/locations
    if not genre or genre == 'all':
      locations = models.Location.all().order('-last_time_updated').fetch(limit, offset)
      if locations:
        max_tracks = 0
        for location in locations:
          if location.track_counter > max_tracks:
            max_tracks = location.track_counter
        return utils.memcache_and_output_array(self, {'max_tracks': max_tracks}, (settings.MAX_TRACKS_CACHE_TIME-5))
      else:
        self.response.out.write("[]") # empty array
      return
                
class LocationsHandler(webapp.RequestHandler):
  """
    Fetching latest updated locations. Returning json
  """
  def get(self):
    
    memcached = memcache.get(self.request.path_qs, namespace='api_cache' )
    if memcached is not None and not util.in_development_enviroment():
      return self.response.out.write(memcached)
    
    # initialization
    locations_array = []
    genre = self.request.get('genre')   
    if self.request.get('limit'):
      limit = int(self.request.get('limit'))
    else:
      limit = settings.FRONTEND_LOCATIONS_LIMIT
    if self.request.get('offset'):
      offset = int(self.request.get('offset'))
    else:
      offset = 0
    if self.request.get('location'):
      return fetch_location_by_id(self, self.request.get('location'))
    
    # Processing latest locations for a certain genre api/locations/?genre={genre_name}
    if genre and genre != 'all':
      if genre not in utils.genres:
        error_response(self, 'unknown_genre', 'Sorry, but we do not know the genre %s.' % genre) 
        return                                                                                   
      location_genres = models.LocationGenreLastUpdate.all().order('-last_time_updated').filter('genre', genre).fetch(limit, offset)
      if location_genres:
        for location_genre in location_genres:
          location_genre.location.track_counter = location_genre.track_counter              
          locations_array.append(create_location_dict(location_genre.location))
        return utils.memcache_and_output_array(self, locations_array)
      else:
        self.response.out.write("[]") # empty array
      return
    
    # Processing latest locations for api/locations
    if not genre or genre == 'all':
      locations = models.Location.all().order('-last_time_updated').fetch(limit, offset)
      if locations:
        for location in locations:
          locations_array.append(utils.create_location_dict(location))
        return utils.memcache_and_output_array(self, locations_array)
      else:
        self.response.out.write("[]") # empty array
      return 
      

class LocationIDHandler(webapp.RequestHandler):
  """
    Fetching tracks. Returning json
  """
  def get(self, location_id=None):

    memcached = memcache.get(self.request.path_qs, namespace='api_cache' )
    if memcached is not None and not util.in_development_enviroment():
      return self.response.out.write(memcached)
    
    if location_id:
      return fetch_location_by_id(self, location_id)
    else:
      error_response(self, 'no_location', 'You have provided no location id.')  
    return    
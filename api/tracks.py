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

import utils
import settings
import models
import api


def fetch_track_by_id(self, track_id): 
  """
    Return track_array with only one track for track_id
  """
  track_array = []
  track = models.Track.all().filter('track_id', int(track_id)).get()
  if track:
    add_to_track_array(track, track_array)
    return memcache_and_output_array(self, track_array)
  else:
    error_response(self, 'track_not_found', 'The track with the track_id %s is not in the datastore.' % track_id)
  return     
           
class TracksHandler(webapp.RequestHandler):
  """
    Fetching tracks. Returning json
  """
  def get(self):
                                              
    memcached = memcache.get(self.request.path_qs, namespace='api_cache' )
    if memcached is not None and not utils.in_development_enviroment():
      return self.response.out.write(memcached)
                          
    # initializing
    track_array = []
    if self.request.get('limit'):
      limit = int(self.request.get('limit'))
    else:
      limit = settings.FRONTEND_LOCATIONS_LIMIT          
    if self.request.get('offset'):
      offset = int(self.request.get('offset'))
    else:
      offset = 0
    
    # Processing for api/tracks/?track=track_id
    if self.request.get('track'):
      return fetch_track_by_id(self, self.request.get('track'))
    
    # Processing for api/tracks/?genre={genre_name} 
    if self.request.get('genre') and self.request.get('genre') != 'all' and not \
       (self.request.get('location') or self.request.get('location_lat') or self.request.get('location_lon')):
      genre = self.request.get('genre')
      if genre not in utils.genres:
        api.utils.error_response(self, 'unknown_genre', 'Sorry, but we do not know the genre %s.' % genre) 
        return
      else:
        tracks = models.Track.all().filter('genre IN', utils.genres.get(genre)).order('-created_at').fetch(limit, offset)
        if tracks:                           
          for track in tracks:
            api.utils.add_to_track_array(track, track_array)
          return api.utils.memcache_and_output_array(self, track_array, utils.genres.get(genre)[0])
        else:
          self.response.out.write("[]") # empty array
        return           
    
    # Processing for api/tracks/?location=location_id
    if self.request.get('location') and (self.request.get('genre') == 'all' or not self.request.get('genre')): 
      location = models.Location.get_by_id(int(self.request.get('location')))
      if not location:
        api.utils.error_response(self, 'location_not_found', 'The location with the id %s is not in the datastore.' % self.request.get('location'))
      else:
        tracks = models.Track.all().filter('location', location.key()).order('-created_at').fetch(limit, offset)
        if tracks:
          for track in tracks:
            api.utils.add_to_track_array(track, track_array)              
          return api.utils.memcache_and_output_array(self, track_array, location.city)
        else:
          self.response.out.write("[]") # empty array
      return
      
    # Processing for api/tracks/?location=location_id&genre={genre_name}  
    if self.request.get('location') and self.request.get('genre'):
      genre = self.request.get('genre')
      if genre not in utils.genres:
        api.utils.error_response(self, 'unknown_genre', 'Sorry, but we do not know the genre %s.' % genre) 
        return
      location = models.Location.get_by_id(int(self.request.get('location')))
      if not location:
        api.utils.error_response(self, 'location_not_found', 'The location with the id %s is not in the datastore.' % self.request.get('location'))
        return
      else:
        tracks = models.Track.all().filter('location', location.key()).filter('genre IN', utils.genres.get(genre))
        tracks = tracks.order('-created_at').fetch(limit, offset)
        if tracks:
          for track in tracks:
            api.utils.add_to_track_array(track, track_array)              
          return api.utils.memcache_and_output_array(self, track_array, (location.city + "_" + utils.genres.get(genre)[0]))
        else:
          self.response.out.write("[]") # empty array
      return
      
    # Processing for api/tracks and api/tracks/?genre=all
    if (self.request.get('genre') == 'all' or not self.request.get('genre')) and not \
       (self.request.get('location') or self.request.get('location_lat') or self.request.get('location_lon')): 
      tracks = models.Track.all().order('-created_at').fetch(limit, offset)
      if tracks:                           
        for track in tracks:
          api.utils.add_to_track_array(track, track_array)
        return api.utils.memcache_and_output_array(self, track_array)
      else:
        self.response.out.write("[]") # empty array
      return      

class TrackIDHandler(webapp.RequestHandler):
  """
    Fetching tracks. Returning json
  """
  def get(self, track_id=None): 

    memcached = memcache.get(self.request.path_qs, namespace='api_cache' )
    if memcached is not None and not utils.in_development_enviroment():
      return self.response.out.write(memcached)   
        
    if track_id:
      return api.utils.fetch_track_by_id(self, track_id)
    else:
      api.utils.error_response(self, 'no_track', 'You have provided no track id.')  
    return
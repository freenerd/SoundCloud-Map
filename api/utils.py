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

from google.appengine.ext.webapp import template
from google.appengine.api import memcache
from django.utils import simplejson as json

import logging
import os
import datetime
import time

import models
import settings

def create_location_dict(location, track_counter = None):
   location_dict = {'lon': location.location.lon,
                   'lat': location.location.lat,
                   'id' : location.key().id(),
                   'city': location.city,
                   'country': location.country,
                   'track_counter': track_counter or location.track_counter,
                   'last_time_updated': location.last_time_updated.isoformat(' ')}   
   return location_dict

def add_to_track_array(track, track_array): 
  """
    filling an array with all the track, location and user data per track 
  """
  
  user_dict = {'id': track.user.user_id,
               'permalink': track.user.permalink,
               'permalink_url': track.user.permalink_url,
               'username': track.user.username,
               'fullname': track.user.fullname,
               'avatar_url': track.user.avatar_url}

  if track.track_id < 0:
    track_array.append({'id': track.track_id,
                        'user': user_dict})
    return
    
  location_dict = create_location_dict(track.user.location)    
   
  track_array.append({  'error': False,
                        'id': track.track_id,
                        'permalink': track.permalink, 
                        'permalink_url': track.permalink_url, 
                        'title': track.title,
                        \
                        'waveform_url': track.waveform_url,
                        'stream_url': track.stream_url, 
                        'artwork_url': track.artwork_url,
                        \
                        'created_at': track.created_at.isoformat(' '),
                        'created_minutes_ago': track.created_minutes_ago(),
                        'downloadable': track.downloadable,
                        'license': track.license,
                        'genre': track.genre,
                        'duration': track.duration,
                        \
                        'location': location_dict,
                        'user': user_dict})                            

def empty_track(user):
  class EmptyTrack:
    def __init__(self, user):
      self.track_id = -time.time()
      self.user = user
  return EmptyTrack(user)
  
def memcache_and_output_array(self, array, xspf_prefix="latest", time=(settings.API_QUERY_INTERVAL*60-5), memcache_name_suffix=''):  
  """
    Save to memcache and output as plain json
  """ 
  self.response.headers.__delitem__('Cache-Control')
  self.response.headers.add_header('Cache-Control', ('max-age='+str(60)))  
  logging.info(self.request.path)
  if self.request.path.replace("/","").split(".")[-1] == "xspf":
    self.response.headers["Content-Type"] = "application/xspf+xml"
    self.response.headers.add_header('Content-Disposition', 'attachment', filename=xspf_prefix+'_tracksonamap.xspf')
    
    path = os.path.join(os.path.dirname(__file__), 'templates/xspf')
    output = template.render(path, { 'array' : array, 
                                     'prefix' : xspf_prefix.replace("_", " ").title(), 
                                     'date' : datetime.datetime.now().isoformat() })
  else:
    output = json.dumps(array)  
  memcache.add(self.request.path_qs+str(memcache_name_suffix), 
               output,
               time=time, 
               namespace='api_cache')
  self.response.out.write(output)                          
  return

def error_response(self, error_name, error_description, error_code = 500):
  """
    Output error as json  
  """
  error_response = {'error': True, 'error_name': error_name, 'error_description': error_description}
  self.response.set_status(error_code)
  self.response.out.write(json.dumps(error_response))

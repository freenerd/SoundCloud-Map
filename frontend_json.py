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
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from django.utils import simplejson as json

import logging

import os
import urllib
import re

import models
import utils
import settings

class MainHandler(webapp.RequestHandler):
	"""
	This script returns JSON-formatted tracks.
	""" 
	
	def add_to_track_array(self, track, track_array, location = None):
		if not location:
			 location =  str(track.location_lat) + "/" + str(track.location_lng) 
		location_track_counter = models.LocationTracksCounter.get_by_key_name(location)	 
		track_array.append({  'track_id' : track.track_id,
													'title' : track.title,
													'permalink' : track.permalink,
													'username' : track.username,
													'user_permalink' : track.user_permalink,
													'avatar_url' : track.avatar_url,
													'artwork_url' : track.artwork_url,
													'location_lng' : track.location_lng,
													'location_lat' : track.location_lat,                                 
													'city' : track.city,
													'country' : track.country,
													'tracks_in_location' : getattr(location_track_counter, 'counter', 1), 
													'created_at' : "new Date(\"%s\")" % track.created_at.ctime(),
													'created_minutes_ago' : track.created_minutes_ago(),
													'waveform_url' : track.waveform_url,
													'stream_url': track.stream_url})	
	
	def get(self): 
		
		split_uri = (self.request.uri).split('/')
		query_all = "ORDER BY __key__ DESC LIMIT " + str(settings.FRONTEND_TRACKS_LIMIT)
		has_been_query_for_all = False
				
		if re.search("genre", self.request.uri):
			genre = split_uri[-1]                 
			query_genre = "WHERE genre IN :1 " + query_all 
			if genre == 'house': 
				tracks = models.TrackCache.gql(query_genre, utils.genre_house)
			elif genre == 'techno': 
				tracks = models.TrackCache.gql(query_genre, utils.genre_techno)  
			elif genre == 'dubstep': 
				tracks = models.TrackCache.gql(query_genre, utils.genre_dubstep)	
			elif genre == 'hiphop': 
				tracks = models.TrackCache.gql(query_genre, utils.genre_hiphop)				
			elif genre == 'electronic': 
				tracks = models.TrackCache.gql(query_genre, utils.genre_electronic) 
			elif genre == 'drumandbass': 
				tracks = models.TrackCache.gql(query_genre, utils.genre_drumandbass)
			elif genre == 'trance': 
				tracks = models.TrackCache.gql(query_genre, utils.genre_trance)
			elif genre == 'rock': 
				tracks = models.TrackCache.gql(query_genre, utils.genre_rock)
			elif genre == 'indie': 
				tracks = models.TrackCache.gql(query_genre, utils.genre_indie)
			elif genre == 'pop': 
				tracks = models.TrackCache.gql(query_genre, utils.genre_pop)																				
			elif genre == 'ambient': 
				tracks = models.TrackCache.gql(query_genre, utils.genre_ambient)
			elif genre == 'jazz': 
				tracks = models.TrackCache.gql(query_genre, utils.genre_jazz)
			elif genre == 'classical': 
				tracks = models.TrackCache.gql(query_genre, utils.genre_classical)		
			else: 
				tracks = models.TrackCache.gql(query_all) 
				has_been_query_for_all = True
				
			 
		elif re.search("location", self.request.uri):
			lat = split_uri[-3]
			lng = split_uri[-2]
			tracks = models.TrackCache.gql("WHERE location_lat = :1 AND location_lng = :2", lat, lng) 
			                                                                                          
		else:
			tracks = models.TrackCache.gql(query_all)
			has_been_query_for_all = True   
			                 
		track_array = []
		used_locations = set()
		for track in tracks:
			# a distinct location may only be on the map once because marker on the same position aren't displayed properly
			location = str(track.location_lat) + "/" + str(track.location_lng)
			if location in used_locations: continue
			used_locations.add(location) 																									
			
			# keep track of the top cities 
			if has_been_query_for_all and track.city:
				try:
					utils.top_cities.remove(track.city.strip())
				except ValueError:
					pass                    
			self.add_to_track_array(track, track_array, location)
		
		# if not all top cities are included, try to add them
		if has_been_query_for_all: 
			if utils.top_cities:
				for city in utils.top_cities:
					 new_track = models.TrackCache.gql("WHERE city = :1 ORDER BY __key__ DESC LIMIT 1", city).get()
					 if new_track:
						  add_to_track_array(track, track_array)
		 											    
		tracks_json = json.dumps(track_array)
		self.response.out.write(tracks_json)

def main():
  application = webapp.WSGIApplication([('/frontend-json/', MainHandler),
																				('/frontend-json/.*', MainHandler),], debug=utils.in_development_enviroment())
  run_wsgi_app(application)

if __name__ == '__main__':
  main()
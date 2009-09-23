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

def add_to_track_array(track, track_array):
	location_dict = {'lon': track.user.location.location.lon,
	 								 'lat': track.user.location.location.lat,
									 'city': track.user.location.city,
									 'country': track.user.location.country,
									 'track_counter': track.user.location.track_counter,
									 'last_time_updated': track.user.location.last_time_updated.isoformat(' ')}
	
	user_dict = {'user_id': track.user.user_id,
							 'permalink': track.user.permalink,
							 'permalink_url': track.user.permalink_url,
							 'username': track.user.username,
							 'fullname': track.user.fullname,
							 'avatar_url': track.user.avatar_url}
	 
	track_array.append({	'error': False,
												'track_id': track.track_id,
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

def error_response(self, error_name, error_description):
	"""
		Output error as json  
	"""
	error_response = {'error': True, 'error_name': error_name, 'error_description': error_description}
	self.response.out.write(json.dumps(error_response))
	
class MainHandler(webapp.RequestHandler):
	"""
	This script returns JSON-formatted tracks.
	""" 
	
	def get(self): 
		
		track_array = [] 
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
			# typical location uri is http://localhost:8080/frontend-json/location/-0.1262362/51.5001524/50/
			lat = split_uri[-4]
			lng = split_uri[-3]
			limit = split_uri[-2]
			tracks = models.TrackCache.gql("WHERE location_lat = :1 AND location_lng = :2 ORDER BY __key__ DESC LIMIT " + limit, lat, lng)   
			for track in tracks.fetch(int(limit)):
				self.add_to_track_array(track, track_array, lat + "/" + lng) 
			tracks_json = json.dumps(track_array)                          
			self.response.out.write(tracks_json) # finished processing script 
			return
			                                                                                     
		else:
			tracks = models.TrackCache.gql(query_all)
			has_been_query_for_all = True   
			                 
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
		
		#if not all top cities are included, try to add them
		if has_been_query_for_all: 
			if utils.top_cities:
				for city in utils.top_cities:
					 new_track = models.TrackCache.gql("WHERE city = :1 ORDER BY __key__ DESC LIMIT 1", city).get()
					 if new_track:
						  self.add_to_track_array(track, track_array)     
		 											    
		tracks_json = json.dumps(track_array)
		self.response.out.write(tracks_json)
		return


class TracksHandler(webapp.RequestHandler):
	"""
		Fetching tracks. Returning json
	"""
	def get(self):
		
		# initializing
		track_array = []
		if self.request.get('limit'):
			limit = self.request.get('limit')
		else:
			limit = str(settings.FRONTEND_TRACKS_LIMIT)
		main_query = 'ORDER BY __key__ DESC LIMIT ' + limit
		
		# Processing for api/tracks/?track_id=track_id
		if self.request.get('track_id'):
			track = models.Track.all().filter('track_id', int(self.request.get('track_id'))).get() 
			if track:
				add_to_track_array(track, track_array)
				self.response.out.write(track_array)
			else:
				error_response(self, 'track_not_found', 'The track with the track_id %s is not in the datastore.' % self.request.get('track_id'))
			return
		
		# Processing for api/tracks/ and api/tracks/?genre=all
		if self.request.get('genre') == 'all' or \
			 (not self.request.get('genre') and not self.request.get('location')):
			tracks = models.Track.gql(main_query)
			if tracks:													 
				for track in tracks:
					add_to_track_array(track, track_array)
				self.response.out.write(track_array)
			else:
				error_response(self, 'no_tracks', 'There are no tracks in the datastore.') 
			return
			
		# Processing for api/tracks/?genre={genre_name} 
		
		if self.request.get('genre'):
			genre = self.request.get('genre')
			if genre not in utils.genres:
				error_response(self, 'unknown_genre', 'Sorry, but we do not know the genre %s.' % genre) 
				return
			else:
				genre_query = 'WHERE genre IN :1 ' + main_query
				tracks = models.Track.gql(genre_query, utils.genres.get(genre)).fetch(int(limit))
				if tracks:													 
					for track in tracks:
						add_to_track_array(track, track_array)
					self.response.out.write(track_array)
				else:
					error_response(self, 'no_tracks_in_genre', 'There are no tracks of the genre %s in the datastore.' % genre)
				return					 
				
class LocationsHandler(webapp.RequestHandler):
	"""
		Fetching tracks. Returning json
	"""
	def get(self):
		pass

def main():
  application = webapp.WSGIApplication([('/api/tracks/.*', TracksHandler),
																				('/api/locations/.*', LocationsHandler),], debug=utils.in_development_enviroment())
  run_wsgi_app(application)

if __name__ == '__main__':
  main()
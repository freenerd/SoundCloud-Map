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
	"""
		filling an array with all the track, location and user data per track 
	"""
	location_dict = {'lon': track.user.location.location.lon,
	 								 'lat': track.user.location.location.lat,
									 'id' : track.user.location.key().id(),
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
	
class TracksHandler(webapp.RequestHandler):
	"""
		Fetching tracks. Returning json
	"""
	def get(self):
		
		# initializing
		track_array = []
		if self.request.get('limit'):
			limit = int(self.request.get('limit'))
		else:
			limit = settings.FRONTEND_TRACKS_LIMIT          
				
		# Processing for api/tracks/?track_id=track_id
		if self.request.get('track_id'):
			track = models.Track.get_by_id(int(self.request.get('track_id')))
			if track:
				add_to_track_array(track, track_array)
				self.response.out.write(json.dumps(track_array))
			else:
				error_response(self, 'track_not_found', 'The track with the track_id %s is not in the datastore.' % self.request.get('track_id'))
			return
		
		# Processing for api/tracks/?genre={genre_name} 
		if self.request.get('genre') and self.request.get('genre') != 'all' and not \
			 (self.request.get('location') or self.request.get('location_lat') or self.request.get('location_lon')):
			genre = self.request.get('genre')
			if genre not in utils.genres:
				error_response(self, 'unknown_genre', 'Sorry, but we do not know the genre %s.' % genre) 
				return
			else:
				tracks = models.Track.all().filter('genre IN', utils.genres.get(genre)).order('-created_at').fetch(limit)
				if tracks:													 
					for track in tracks:
						add_to_track_array(track, track_array)
					self.response.out.write(json.dumps(track_array))
				else:
					error_response(self, 'no_tracks_in_genre', 'There are no tracks of the genre %s in the datastore.' % genre)
				return					 
		
		# Processing for api/tracks/?location=location_id
		if self.request.get('location') and not self.request.get('genre'): 
			location = models.Location.get_by_id(int(self.request.get('location')))
			if not location:
				error_response(self, 'location_not_found', 'The location with the id %s is not in the datastore.' % self.request.get('location'))
			else:
				users = models.User.all().filter('location', location.key()).fetch(limit)
				if users:
					for user in users:                     
						tracks = models.Track.all().filter('user', user.key()).fetch(limit)
						for track in tracks:
							add_to_track_array(track, track_array)
					self.response.out.write(json.dumps(track_array))
				else:
					error_response(self, 'no_tracks_in_location', 'There are no tracks at the location %s in the datastore.' % self.request.get('location'))
			return
			
		# Processing for api/tracks/?location=location_id&genre={genre_name}	
		if self.request.get('location') and self.request.get('genre'):
			genre = self.request.get('genre')
			if genre not in utils.genres:
				error_response(self, 'unknown_genre', 'Sorry, but we do not know the genre %s.' % genre) 
				return
			location = models.Location.get_by_id(int(self.request.get('location')))
			if not location:
				error_response(self, 'location_not_found', 'The location with the id %s is not in the datastore.' % self.request.get('location'))
				return
			else:
				users = models.User.all().filter('location', location.key()).fetch(limit)
				if users:
					for user in users:                     
						tracks = models.Track.all().filter('user', user.key()).filter('genre IN', utils.genres.get(genre)).fetch(int(limit))
						for track in tracks:
							add_to_track_array(track, track_array)
					self.response.out.write(json.dumps(track_array))
				else:
					error_response(self, 'no_tracks_in_location', 'There are no tracks at the location %s in the datastore.' % self.request.get('location'))
			return
			
		# Processing for api/tracks/ and api/tracks/?genre=all
		if (self.request.get('genre') == 'all' or not self.request.get('genre')) and not \
		 	 (self.request.get('location') or self.request.get('location_lat') or self.request.get('location_lon')): 
			tracks = models.Track.all().order('-created_at').fetch(limit)
			if tracks:													 
				for track in tracks:
					add_to_track_array(track, track_array)
				self.response.out.write(json.dumps(track_array))
			else:
				error_response(self, 'no_tracks', 'There are no tracks in the datastore.') 
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
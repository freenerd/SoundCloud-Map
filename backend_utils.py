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

from google.appengine.api.urlfetch_errors import DownloadError
from google.appengine.api import urlfetch
from google.appengine.ext import db 
from django.utils import simplejson as json

import logging
import datetime, time

import models     
import utils
import settings
import urllib
			
def open_remote_api(query, api):
	"""
	Calls a remote API with a query. Returns json.
	Google App Enging sometimes fails to open the URL properly resulting in a DownloadError.
	So we have to do it more often sometimes ...
	"""
	if api == "soundcloud":
		api_url = settings.SOUNDCLOUD_API_URL
		api_name = "SoundCloud API"
	if api == "googlemaps":
		api_url = settings.GOOGLE_MAPS_API_URL
		api_name = "Google Maps API"
	
	query = api_url + query
	
	logging.info("Requesting %s with uri: %s" % (api_name, query))

	i = 0
	while True:
		if (i >= settings.API_RETRIES):
			break
		try:
			result = urlfetch.fetch(query, deadline=10) # raises DownloadError sometimes
			i = 0
			break
		except DownloadError:
			pass
		i += 1

	if i != 0:
		logging.error("Connection to %s failed." % api_name)
		raise DownloadError("Connection to %s failed." % api_name)
	return json.loads(result.content)

def get_latest_tracks_from_soundcloud():
	"""
	Get Latest Tracks from Soundcloud
	"""
	created_at_time = datetime.datetime.now()
	created_at_time -= datetime.timedelta(hours=settings.SOUNDCLOUD_TIMEZONE_ADJUSTMENT)
	created_at_time -= datetime.timedelta(minutes=settings.API_QUERY_INTERVAL)
	query = "/tracks.json?created_at[from]=%s&duration[to]=%s" % (created_at_time.isoformat(), settings.DURATION_LIMIT)
	tracks = open_remote_api(query, "soundcloud")	
	return tracks	

def update_location_genre_data(track, location):
	# determine genre for track
	track_genre = None
	for genre in utils.genres.iteritems():
		if track['genre'] and track['genre'].strip().lower() in genre[1]:
			track_genre = genre[0]
	# update LocationGenreLastUpdate						 
	if track_genre:
		location_genre = models.LocationGenreLastUpdate.all().filter('location', location.key()).filter('genre', track_genre).get()
		if location_genre:
			location_genre.last_time_updated = datetime.datetime.now() 
			location_genre.track_counter += 1
			location_genre.put()
		else:
			location_genre = models.LocationGenreLastUpdate( \
										 					location = location.key(),
															genre = track_genre,
															track_counter = 1,
															last_time_updated = datetime.datetime.now())
			location_genre.put()
		logging.info("Updated location genre for genre %s and track_count: %i in location lat/lon %s/%s in city: %s country: %s." % \
								(track_genre, location_genre.track_counter, location.location.lat, location.location.lon, location.city, location.country))	
	return

def update_location_data(track, location):
	# update Location
	location.track_counter += 1
	location.last_time_updated = datetime.datetime.now()
	location.put()                
	logging.info("Updated location lat/lon %s/%s in city: %s country: %s and track_count: %i." % \
							(location.location.lat, location.location.lon, location.city, location.country, location.track_counter))
	update_location_genre_data(track, location)
	return

def write_track_to_datastore(track, user, location):
	"""
	Get a list of tracks and save them to the database
	Return the number of track saved
	""" 
	logging.info("Saving track \"%s\" by \"%s\" (id: %s, created at: %s) to datastore ..." % \
							(track['title'], user.username, track['id'], track['created_at']))		
	created_at = datetime.datetime.strptime(track['created_at'], "%Y/%m/%d %H:%M:%S +0000")
	release_date = datetime.date(year=int(track['release_year'] or 1900), month=int(track['release_month'] or 1), day=int(track['release_day'] or 1))
	if track['genre']:
		genre = track['genre'].strip().lower()
	else:
		genre = ''
				
	new_track = models.Track( \
		track_id = int(track['id']), 
		permalink = track['permalink'], 
		permalink_url = track['permalink_url'],				
		title = track['title'],
		\
		stream_url = track['stream_url'],
		waveform_url = track['waveform_url'],
		artwork_url = track['artwork_url'],
		purchase_url = track['purchase_url'],
		\
		created_at = created_at,
		downloadable = track['downloadable'],        
		original_format = track['original_format'],
		release_date = release_date,
		release = track['release'],
		isrc = track['isrc'],
		label_name = track['label_name'],
		label_id = track['label_id'],
		license = track['license'],
		genre = genre,
		bpm = track['bpm'],
		key_signature = track['key_signature'],
		duration = track['duration'],
		description = track['description'],
    \
		user = user.key(),
		location = location.key())			   
	new_track.put()
	logging.info("Track saved to datastore.")                                    
			
def get_location(city, country):
	"""
	Get a city and a country and try to find out the location via the Google Maps API
	Returns a dictionary with location, country and city
	"""
	if not city and not country:
		raise RuntimeError, "Cannot be localized"

	location_query = (city or '') + " " + (country or '')
	location_query = urllib.quote(location_query.strip().encode('utf-8'))
	query = "&q=%s&output=json&oe=utf8" % location_query
 
	position = open_remote_api(query, "googlemaps")

	if position:
		lng = lat = 0
				
		if position['Status']['code'] == 200:
			# 200 = "Success"
			lon = unicode(position['Placemark'][0]['Point']['coordinates'][0])
			lat = unicode(position['Placemark'][0]['Point']['coordinates'][1])     
			try:                                                               
				country = unicode(position['Placemark'][0]['AddressDetails']['Country']['CountryName'])
			except KeyError:
				logging.info("No Country found in %s" % unicode(dict(position)))
				country = None  
			try:
				if 'SubAdministrativeArea' in position['Placemark'][0]['AddressDetails']['Country']['AdministrativeArea']:                                            
					city = 	unicode(position['Placemark'][0]['AddressDetails']['Country']['AdministrativeArea']['SubAdministrativeArea']['Locality']['LocalityName'])
				else:
					city = 	unicode(position['Placemark'][0]['AddressDetails']['Country']['AdministrativeArea']['Locality']['LocalityName']) 
			except KeyError:
				logging.info("No City found in %s" % unicode(dict(position)))
				city = None
				
			time.sleep(1) # wait to avoid Google Maps' 620 "Too many requests" error in next query
			return {'location': db.GeoPt(lat,lon), 'country': country, 'city': city}
			
		if position['Status']['code'] in (602, 603):
			# 602 and 603 = "Address could not be localized"
			raise RuntimeError, "Cannot be localized"
			
		else:
			# Something worse must have happened than just not being able to find an address
			logging.error("Localization via maps.google.com failed with error code %i" % position['Status']['code'])
			
	raise RuntimeError, "Cannot be localized"    
			
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
	
def write_track_to_cache(track, user):
	"""
	Get a list of tracks and save them to the database
	Return the number of track saved
	"""
	created_at = datetime.datetime.strptime(track['created_at'], "%Y/%m/%d %H:%M:%S +0000")
	release_date = datetime.date(year=int(track['release_year'] or 1900), month=int(track['release_month'] or 1), day=int(track['release_day'] or 1))		
	new_track = models.Track( \
		ID = int(track['id']), 
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
		genre = track['genre'].strip().lower(),
		bpm = track['bpm'],
		key_signature = track['key_signature'],
		duration = track['duration'],
		description = track['description'],
    \
		user = user.key())			
	logging.info("Saving to DB: Track \"%s\" by \"%s\" (%s)." % (track['title'], user.username, track['created_at']))	   
	new_track.put()
	#update_location_tracks_counter(track)                                      
		
def cleanup_cache():
	"""
	Remove all old tracks from database
	"""
	delete_older_than = datetime.datetime.now()
	delete_older_than -= datetime.timedelta(hours=settings.SOUNDCLOUD_TIMEZONE_ADJUSTMENT)
	delete_older_than -= datetime.timedelta(minutes=settings.CLEANUP_INTERVAL)
	logging.info("Cleaning Up Everything Before %s" % delete_older_than.isoformat())	
	
	query = models.TrackCache.gql("WHERE entry_created_at < :1", delete_older_than)
	counter = 0
	for track in query:
		logging.info("Deleting from DB: Track \"%s\" by \"%s\" (%s)." % (track.title, track.username, track.created_at))
		track.delete()
		counter += 1	
	return counter
	
	
def get_location(city, country):
	"""
	Get a city and a country and try to get a location via the Google Maps API
	Returns a tuple (latitude, longitude)
	"""
	if not city and not country:
		raise RuntimeError, "Cannot be localized"

	location_query = (city or '') + " " + (country or '')
	location_query = urllib.quote(location_query.strip().encode('utf-8'))
	query = "&q=%s&output=json&oe=utf8" % location_query
 
	position = open_remote_api(query, "googlemaps")

	if position:
		lng = lat = 0
		logging.info("Returned object from api is: %s" % unicode(dict(position)))
				
		if position['Status']['code'] == 200:
			# 200 = "Success"
			lon = unicode(position['Placemark'][0]['Point']['coordinates'][0])
			lat = unicode(position['Placemark'][0]['Point']['coordinates'][1]) 
			from_api_country = position['Placemark'][0]['AddressDetails']['Country']    
			try:
				country = unicode(from_api_country['CountryName'])
			except KeyError:
				country = None  
			try:
				if 'SubAdministrativeArea' in from_api_country['AdministrativeArea']:                                            
					city = 	unicode(from_api_country['AdministrativeArea']['SubAdministrativeArea']['Locality']['LocalityName'])
				else:
					city = 	unicode(from_api_country['AdministrativeArea']['Locality']['LocalityName']) 
			except KeyError:
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
	
def update_location_tracks_counter(track, increase = True):	
	location_track_counter = models.LocationTracksCounter.gql("WHERE location_lng = :1 AND location_lat = :2", \
																														unicode(track['location_lng']), unicode(track['location_lat'])).get()																											
																																																									
	if hasattr(location_track_counter, 'counter'):  
		if increase:
			location_track_counter.counter += 1
		else:
			location_track_counter.counter -= 1 
		location_track_counter.put() 
 		logging.info("Updated Location Track Counter for location %s / %s (city: %s) to %i" % \
 									(location_track_counter.location_lat, location_track_counter.location_lng, \
									 location_track_counter.city, location_track_counter.counter))
	else:
		new_location_track_counter = models.LocationTracksCounter( \
			key_name = unicode(track['location_lat'] + "/" + track['location_lng']),
			location_lat = unicode(track['location_lat']), 
			location_lng = unicode(track['location_lng']),
			city = unicode(track['city']),
			country = unicode(track['country']),
			counter = 1)
		new_location_track_counter.put()
 		logging.info("Inserted new Location Track Counter for location %s / %s (city: %s) to %i" % \
 									(new_location_track_counter.location_lat, new_location_track_counter.location_lng, new_location_track_counter.city, new_location_track_counter.counter))
		
			
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
from django.utils import simplejson as json

import logging
import datetime, time

import models
import utils
import settings
import urllib

def open_soundcloud_api(query):
	"""
	Calls the Soundcloud API and appends the query. Returns plaintext result.
	Query needs a leading Slash / like "/tracks"
	Google App Enging sometimes fails to open the URL properly resulting in a DownloadError.
	So we have to do it more often sometimes ...
	"""

	logging.info("SoundCloud API request url: %s" %	settings.SOUNDCLOUD_API_URL + query)

	i = 0
	while True:
		if (i >= settings.API_RETRIES):
			break
		try:
			result = urlfetch.fetch(settings.SOUNDCLOUD_API_URL + query, deadline=10) # raises DownloadError sometimes
			i = 0
			break
		except DownloadError:
			pass
		i += 1

	if i != 0:
		logging.error("Connection to SoundCloud API failed with URL %s" % (settings.SOUNDCLOUD_API_URL + query))
		raise DownloadError("Connection to SoundCloud API failed.")
	return result.content

def get_latest_tracks_from_soundcloud():
	"""
	Get Latest Tracks from Soundcloud
	"""
	created_at_time = datetime.datetime.now()
	created_at_time -= datetime.timedelta(hours=settings.SOUNDCLOUD_TIMEZONE_ADJUSTMENT)
	created_at_time -= datetime.timedelta(minutes=settings.API_QUERY_INTERVAL)
	tracks = open_soundcloud_api("/tracks.json?created_at[from]=%s" % created_at_time.isoformat())
	tracks = json.loads(tracks)
	return tracks
	
	
def remove_duplicate_users(tracks):
	"""
	Takes a list of tracks and searches for tracks by the same user. 
	If a user has uploaded several tracks, only the most recent will be returned.
	Returns a list of tracks from distinct users.
	"""
	done_tracks_permalinks = set()
	done_tracks = []
	i = 0
	
	for track in tracks:
		if track['user']['permalink'] in done_tracks_permalinks:
			i += 1
			continue
		else:
			done_tracks_permalinks.add(track['user']['permalink'])
			done_tracks.append(track)
	
	logging.info("%i duplicates by user removed" % i)
	return done_tracks
		

def remove_unusable_tracks(tracks):
	"""
	Removes Tracks that do not fit our quality needs
	"""
	done_tracks = []
	i = 0
	
	for track in tracks:
		if not track['streamable'] or track['sharing'] != 'public':
			i += 1
			continue
		else:
			done_tracks.append(track)

	logging.info("%i tracks removed because they did not fit our quality needs." % i)
	return done_tracks


def add_complete_user_data(tracks):
	"""
	Takes a list of tracks.	Adds the complete user data for the track.
	Returns a list with all new tracks and user data in track['user']
	This makes a query to the Soundcloud API and Google Maps for every track!
	"""		
	new_tracks = []
	logging.info("Having a look at %i tracks for Complete User Data." % len(tracks))
	counter = {'no_location':0}
	for track in tracks:	
		# fetch user data
		userdata = open_soundcloud_api("/users/%s.json" % track['user']['permalink'])
		userdata = json.loads(userdata)
		track['user'] = userdata                                                                                    
		logging.info("user: %s", track)
		# logging.info("Having a look at the complete user data of track %s by user %s (city: %s / country: %s)" % )
		# localize
		try:        
			location = get_location(track['user']['city'], track['user']['country'])
			track['location_lat'] = location['lat']
			track['location_lng'] = location['lng']
			track['city'] = location['city'] or track.get('city', None)
			track['country'] = location['country'] or track.get('country', None) 						
			logging.info("Location for User \"%s\" is %s / %s." % (track['user']['username'], track['location_lat'], track['location_lng']))
		except RuntimeError:
			logging.info("No Location for User \"%s\" with City/Country: \"%s / %s\"." % (track['user']['username'], track['user']['city'], track['user']['country']))
			counter['no_location'] += 1			
			continue # does not need to be added to new_tracks because no localization data
		new_tracks.append(track)
		logging.info("Userdata for User \"%s\" from \"%s / %s\" fetched." % (track['user']['username'], track['user']['city'], track['user']['country']))	
	logging.info("%i new tracks could not be localized." % counter['no_location'])	
	return new_tracks
	
	
def write_tracks_to_cache(tracks):
	"""
	Get a list of tracks and save them to the database
	Return the number of track saved
	"""
	counter = 0
	for track in tracks:
		created_at = datetime.datetime.strptime(track['created_at'], "%Y/%m/%d %H:%M:%S +0000")		
		new_track = models.TrackCache( \
			track_id = int(track['id']),
			title = track['title'],
			permalink = track['permalink'],
			permalink_url = track['permalink_url'],
			created_at = created_at,
			stream_url = track['stream_url'],
			waveform_url = track['waveform_url'],
			downloadable = track['downloadable'],
			artwork_url = track['artwork_url'],
			genre = track['genre'].strip().lower(),
			username = track['user']['username'],
			fullname = track['user']['full_name'],
			location_lng = (track['location_lng'] or ''),
			location_lat = (track['location_lat'] or ''),
			city = track['city'],
			country = track['country'],					
			user_id = track['user']['id'],
			user_permalink = track['user']['permalink'],
			avatar_url = track['user']['avatar_url'])			
		logging.info("Saving to DB: Track \"%s\" by \"%s\" (%s)." % (track['title'], track['user']['username'], track['created_at']))	   
		new_track.put()
		update_location_tracks_counter(track)
		
	counter += 1 	
	return counter
		
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

	location = (city or '') + " " + (country or '')
	location = urllib.quote(location.strip().encode('utf-8'))
	url = "http://maps.google.com/maps/geo?key=%s&q=%s&output=json&oe=utf8" % (settings.GOOGLE_MAPS_API_KEY, location)

	logging.info("Google Maps API request url: %s" % url)

	# Sometimes urlfetch.fetch fails, so we try several times
	i = 0
	while True:
		if (i >= settings.API_RETRIES):
			break
		try:
			position = urlfetch.fetch(url, deadline=10) # raises DownloadError sometimes
			i = 0
			break
		except DownloadError:
			pass
		i += 1
		
	if i != 0:
		logging.error("Connection to Google Maps API failed with URL %s" % (url))

	if position:
		lng = lat = 0
		position_object = json.loads(position.content)
		logging.info("Returned object from api is: %s" % unicode(dict(position_object)))
				
		if position_object['Status']['code'] == 200:
			# 200 = "Success"
			lng = unicode(position_object['Placemark'][0]['Point']['coordinates'][1])
			lat = unicode(position_object['Placemark'][0]['Point']['coordinates'][0]) 
			from_api_country = position_object['Placemark'][0]['AddressDetails']['Country']    
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
			return {'lng': lng, 'lat': lat, 'country': country, 'city': city}
			
		if position_object['Status']['code'] in (602, 603):
			# 602 and 603 = "Address could not be localized"
			raise RuntimeError, "Cannot be localized"
			
		else:
			# Something worse must have happened than just not being able to find an address
			logging.error("Localization via maps.google.com failed with error code %i" % position_object['Status']['code'])
			
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
		
			
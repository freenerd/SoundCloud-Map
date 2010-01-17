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

from google.appengine.runtime import DeadlineExceededError
from google.appengine.api.labs import taskqueue 
from google.appengine.ext import webapp
from google.appengine.ext import db		 
import wsgiref.handlers 
import logging
import os

import backend.utils
import models

class DropDatabase(webapp.RequestHandler):

	def get(self):
		if self.request.get('db') == 'track':
			data = data = models.Track.all()
		if self.request.get('db') == 'trackcache':
			data = data = models.TrackCache.all()		
		if self.request.get('db') == 'location': 
			data = data = models.Location.all().filter('city', 'None')					
		if self.request.get('db') == 'user':
			data = data = models.User.all()
		if self.request.get('db') == 'locationtrackscounter':
			data = data = models.LocationTracksCounter.all()									
		if self.request.get('db') == 'locationgenrelastupdate':
			data = data = models.LocationGenreLastUpdate.all()

		if data:
			try:                       
				logging.info("Data = " + str(data))
 				for x in data.fetch(1000):
					logging.info("X is " + str(x))   
					
					lastupdate = models.LocationGenreLastUpdate.all().filter('location', x.key())
					while True:
						thisupdate = lastupdate.fetch(500)
						if thisupdate:
							logging.info("Deleting some LocationCounters")
							db.delete(thisupdate)
						else:
							break
							
					tracks = models.Track.all().filter('location', x.key()) 
					while True:
						thistracks = tracks.fetch(500)
						if thistracks:
							logging.info("Deleting some tracks")
							db.delete(thistracks)
						else:
							break
							
					user = models.User.all().filter('location', x.key())
					while True:
						thisusers = user.fetch(500)
						if thisusers: 
							logging.info("Deleting some users")
							db.delete(thisusers)
						else:
							break
					
					logging.info("Deleting the Location")		
					db.delete(x)
					 
				if data.fetch(1):  
					queue = taskqueue.Queue()
					queue.add(taskqueue.Task(url='/backend-cleanup/?db='+ self.request.get('db'), method='GET'))
					self.response.out.write("Ran out of time, need to delete more!")
					
			except DeadlineExceededError:
					queue = taskqueue.Queue()
					queue.add(taskqueue.Task(url='/backend-cleanup/?db='+ self.request.get('db'), method='GET'))
					self.response.out.write("Ran out of time, need to delete more!")																	 
		else:
			return

def main():
	wsgiref.handlers.CGIHandler().run(webapp.WSGIApplication([
		('/backend-cleanup/.*', DropDatabase),
	]))			

if __name__ == '__main__':
	main()	

def main_old():
	"""
	This script is inteded to be called by a cronjob to purge all the old tracks from the database cache.
	"""
	try:
		logging.info("Backend Cleanup Started")

		counter_delete = cleanup_cache()
		logging.info("Deleted %i old tracks from DB." % counter_delete)

		logging.info("Backend Cleanup Finished")

	except DeadlineExceededError:
		logging.warning("Backend Cleanup has been canceled due to Deadline Exceeded")
		for name in os.environ.keys():
			logging.info("%s = %s" % (name, os.environ[name]))

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
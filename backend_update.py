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
from google.appengine.api import memcache
import logging
import time
import os

import models
import backend_utils

def main():
	"""
	This method queries the SoundCloud API, fetches the latest tracks having been uploaded
	since the last backend update, and adds them to the task queue for further processing.
	It is intended to be called by a cronjob on a short basis, like every 3 minutes.
	"""
	try:
		logging.info("Backend update started")
		
		logging.info("Fetching latest tracks from SoundCloud")
		tracks = backend_utils.get_latest_tracks_from_soundcloud()
		logging.info("Fetched %i tracks from Soundcloud" % len(tracks))
		if len(tracks) > 0:
			counter = 0    
			for track in tracks:  
				track['id'] = unicode(track['id'])
				if memcache.add(track['id'], track, time=1800, namespace="backend_update_track"):
					taskqueue.add(url='/backend-update/track', params={'track_id': track['id']})
					logging.info("Added track_id %s to memcache and traskqueue." % track['id'])
					counter += 1					
				else:
					logging.error("Setting Memcache failed for track \"%s\" by \"%s\" (id: %s, created at: %s)." % \
											(track['title'], track['user']['username'], track['id'], track['created_at']))
			logging.info("Added %i tracks to the taskqueue" % counter)
		else:
			logging.info("Backend update finished without new tracks") 
		
	except DeadlineExceededError:
		logging.warning("Backend Update has been canceled due to Deadline Exceeded")
		for name in os.environ.keys():
			logging.info("%s = %s" % (name, os.environ[name]))
			
if __name__ == '__main__':
  main()
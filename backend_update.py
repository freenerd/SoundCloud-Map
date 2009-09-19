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
import logging
import time
import os

import models
import backend_utils

def main():
	"""
	This script queries the SoundCloud API, fetches the latest tracks having been uploaded
	since the last backend update, geocodes them and writes them to the database cache.
	It is intended to be called by a cronjob on a short basis, like every 3 minutes.
	"""
	try:
		logging.info("Backend Update Started")
		
		logging.info("Starting to read data from Soundcloud")
		tracks = backend_utils.get_latest_tracks_from_soundcloud()
		logging.info("Got Data from Soundcloud API")
		logging.info("Fetched %i tracks from Soundcloud" % len(tracks))
		if len(tracks) > 0:
			logging.info("Latest track is \"%s\" by \"%s\" (%s)." % \
									 (tracks[0]['title'], tracks[0]['user']['username'], tracks[0]['created_at']))		
			tracks = backend_utils.remove_duplicate_users(tracks)
			tracks = backend_utils.remove_unusable_tracks(tracks)			
			tracks = backend_utils.add_complete_user_data(tracks)
			logging.info("Found %i new tracks" % len(tracks))	
			logging.info("Finished reading data from Soundcloud")
			
			logging.info("Going to write %i new tracks to DB." % len(tracks))	
			counter_write = backend_utils.write_tracks_to_cache(tracks)
			logging.info("Written %i new tracks to DB." % counter_write)
		
		logging.info("Backend Update Finished")

	except DeadlineExceededError:
		logging.warning("Backend Update has been canceled due to Deadline Exceeded")
		for name in os.environ.keys():
			logging.info("%s = %s" % (name, os.environ[name]))
			
if __name__ == '__main__':
  main()
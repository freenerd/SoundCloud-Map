#!/usr/bin/env python

# Copyright (c) 2012 Johan Uhle
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
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import webapp
from google.appengine.ext import db

import wsgiref.handlers
import logging
import os
import datetime

import backend_utils
import models
import utils
import settings

class CleanupHandler(webapp.RequestHandler):
  """ Queue tracks for deletion """

  def get(self):
    try:
      deletion_date_threshold = datetime.datetime.now() 
      deletion_date_threshold -= datetime.timedelta(minutes=settings.CLEANUP_INTERVAL)

      logging.info("Backend cleanup started for tracks older than %s" % deletion_date_threshold.isoformat())

      tracks = models.Track.all().filter("entry_created_at <", deletion_date_threshold).fetch(1000, 0)
      for track in tracks:
        taskqueue.add(url='/backend/cleanup/tracks/%s' % track.key())

      logging.info("Backend cleanup tracks queued up")

    except DeadlineExceededError:
      logging.warning("Backend Cleanup has been canceled due to Deadline Exceeded")
      for name in os.environ.keys():
        logging.info("%s = %s" % (name, os.environ[name]))

class CleanupTrackHandler(webapp.RequestHandler):
  """ Remove track """

  def post(self, track_key=''):
    try:
      logging.info("Backend Cleanup removing track %s" % track_key)

      track = models.Track.get(track_key)

      if track: track.remove()

    except DeadlineExceededError:
      logging.warning("Backend Cleanup has been canceled due to Deadline Exceeded")
      for name in os.environ.keys():
        logging.info("%s = %s" % (name, os.environ[name]))

def main():
  application = webapp.WSGIApplication([
    (r'/backend/cleanup/start', CleanupHandler),
    (r'/backend/cleanup/tracks/([0-9a-zA-Z-_]{1,128})', CleanupTrackHandler)
    ], debug=utils.in_development_enviroment())
  run_wsgi_app(application)

if __name__ == '__main__':
  main()

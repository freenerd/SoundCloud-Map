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

from google.appengine.ext import db

import datetime
import logging

class TrackCache(db.Model):
	
	track_id = db.IntegerProperty(required=True)
	title = db.StringProperty()
	permalink = db.StringProperty()
	permalink_url = db.TextProperty()
	created_at = db.DateTimeProperty()
	stream_url = db.TextProperty()
	waveform_url = db.TextProperty()
	downloadable = db.BooleanProperty()
	artwork_url = db.TextProperty()
	genre = db.StringProperty()
	
	user_id = db.IntegerProperty()
	user_permalink = db.TextProperty()
	username = db.StringProperty()
	fullname = db.TextProperty()
	location_lng = db.StringProperty()
	location_lat = db.StringProperty()	
	city = db.TextProperty()
	country = db.TextProperty()
	avatar_url = db.TextProperty()
	
	entry_created_at = db.DateTimeProperty(auto_now_add=True)
	
	def created_minutes_ago(self):
		timedelta = datetime.datetime.now() - self.created_at
		return (timedelta.seconds / 60)    
		
class LocationTracksCounter(db.Model):
	
	location_lng = db.StringProperty(required=True)
	location_lat = db.StringProperty(required=True)
	city = db.StringProperty()
	country = db.StringProperty()                  
	counter = db.IntegerProperty(required=True)	
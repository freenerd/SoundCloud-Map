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

class Location(db.Model):
	
	location = db.GeoPtProperty(required=True)
	city = db.StringProperty()
	country = db.StringProperty()                  
	track_counter = db.IntegerProperty()

class Track(db.Model):
	
	track_id = db.IntegerProperty(required=True)
	track_permalink = db.StringProperty()
	track_permalink_url = db.LinkProperty()
	title = db.StringProperty()
	
	user_id = db.IntegerProperty()
	user_permalink = db.StringProperty()
	user_permalink_url = db.LinkProperty()
	user_name = db.StringProperty()
	user_fullname = db.StringProperty()

	stream_url = db.LinkProperty()
	waveform_url = db.LinkProperty()
	avatar_url = db.LinkProperty() 
	artwork_url = db.LinkProperty() 
	purchase_url = db.LinkProperty()    
			
	created_at = db.DateTimeProperty()
	downloadable = db.BooleanProperty()
	original_format = db.StringProperty()
	release_date = db.DateProperty()
	release = db.StringProperty()
	iscr = db.StringProperty()   
	label = db.StringProperty()
	label_id = db.IntegerProperty()  
	license = db.StringProperty()
	genre = db.StringProperty()
	bpm = db.FloatProperty()
	key_signature = db.StringProperty()
	duration = db.IntegerProperty()
	description = db.TextProperty()

	location = db.ReferenceProperty(reference_class=Locations)
  	
	entry_created_at = db.DateTimeProperty(auto_now_add=True)
	
	def created_minutes_ago(self):
		timedelta = datetime.datetime.now() - self.created_at 		
		return ((timedelta.seconds + timedelta.days*86400) / 60)     
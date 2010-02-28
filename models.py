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
  last_time_updated = db.DateTimeProperty()      

class LocationGenreLastUpdate(db.Model):
  
  location = db.ReferenceProperty(reference_class=Location)
  genre = db.StringProperty()
  track_counter = db.IntegerProperty()
  last_time_updated = db.DateTimeProperty()
  
class User(db.Model):
  user_id = db.IntegerProperty(required=True)
  permalink = db.StringProperty()
  permalink_url = db.LinkProperty()
  username = db.StringProperty()
  fullname = db.StringProperty()
  avatar_url = db.LinkProperty()      
  location = db.ReferenceProperty(reference_class=Location) 
  twitter_name = db.StringProperty()
  twitter_url = db.LinkProperty()
  twitter_location = db.StringProperty()
  twitter_description = db.StringProperty()

class Track(db.Model):
  
  track_id = db.IntegerProperty(required=True)
  permalink = db.StringProperty()
  permalink_url = db.LinkProperty()
  title = db.StringProperty()
  
  stream_url = db.LinkProperty()
  waveform_url = db.LinkProperty()
  artwork_url = db.LinkProperty() 
  purchase_url = db.LinkProperty()    
      
  created_at = db.DateTimeProperty()
  downloadable = db.BooleanProperty()
  original_format = db.StringProperty()
  release_date = db.DateProperty()
  release = db.StringProperty()
  isrc = db.StringProperty()   
  label_name = db.StringProperty()
  label_id = db.IntegerProperty()  
  license = db.StringProperty()
  genre = db.StringProperty()
  bpm = db.FloatProperty()
  key_signature = db.StringProperty()
  duration = db.IntegerProperty()
  description = db.TextProperty()
  
  user = db.ReferenceProperty(reference_class=User)
  location = db.ReferenceProperty(reference_class=Location)
  entry_created_at = db.DateTimeProperty(auto_now_add=True)
  
  def created_minutes_ago(self):
    timedelta = datetime.datetime.now() - self.created_at     
    return ((timedelta.seconds + timedelta.days*86400) / 60)
    
class SoundCloudConnectUser(db.Model):
  authorized = db.BooleanProperty()
  token = db.StringProperty(required=True)
  secret = db.StringProperty(required=True)
  user_id = db.IntegerProperty()
  session_hash = db.StringProperty()
  max_location_followers_count = db.IntegerProperty()
  max_location_followings_count = db.IntegerProperty()  
  max_location_favorites_count = db.IntegerProperty()  
  followers = db.IntegerProperty()  
  followings = db.IntegerProperty()  
  favorites = db.IntegerProperty()  
  processed_followers = db.IntegerProperty()  
  processed_followings = db.IntegerProperty()  
  processed_favorites = db.IntegerProperty()      
  geolocated_followers = db.IntegerProperty()  
  geolocated_followings = db.IntegerProperty()  
  geolocated_favorites = db.IntegerProperty()  
  
  entry_created_at = db.DateTimeProperty(auto_now_add=True)
  
class SoundCloudConnectUserLocation(db.Model):
  follower_count = db.IntegerProperty()
  following_count = db.IntegerProperty()  
  favorite_count = db.IntegerProperty()

  soundcloudconnect_user = db.ReferenceProperty(reference_class=SoundCloudConnectUser)
  location = db.ReferenceProperty(reference_class=Location)
  entry_created_at = db.DateTimeProperty(auto_now_add=True)

class SoundCloudConnectFollower(db.Model):
  soundcloudconnect_user = db.ReferenceProperty(reference_class=SoundCloudConnectUser)
  user = db.ReferenceProperty(reference_class=User)  
  location = db.ReferenceProperty(reference_class=Location)
  entry_created_at = db.DateTimeProperty(auto_now_add=True)  
  
class SoundCloudConnectFollowing(db.Model):
  soundcloudconnect_user = db.ReferenceProperty(reference_class=SoundCloudConnectUser)
  user = db.ReferenceProperty(reference_class=User)  
  location = db.ReferenceProperty(reference_class=Location)
  entry_created_at = db.DateTimeProperty(auto_now_add=True)  
  
class SoundCloudConnectFavorite(db.Model):
  soundcloudconnect_user = db.ReferenceProperty(reference_class=SoundCloudConnectUser)
  track = db.ReferenceProperty(reference_class=Track)  
  location = db.ReferenceProperty(reference_class=Location)
  entry_created_at = db.DateTimeProperty(auto_now_add=True)    
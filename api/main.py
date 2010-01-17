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

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

import util
from api import tracks
from api import locations
from api.soundcloudconnect import main as scconnect_main, favorites
from api.soundcloudconnect import followers
from api.soundcloudconnect import followings

def main():
  application = webapp.WSGIApplication([(r'/api/tracks/([0-9]{1,64})', tracks.TrackIDHandler),
                                        ('/api/tracks.*', tracks.TracksHandler),
                                        ('/api/locations/maxtracks.*', locations.MaxTracksHandler),
                                        (r'/api/locations/([0-9]{1,64})', locations.LocationIDHandler),
                                        ('/api/soundcloud-connect/', scconnect_main.SoundCloudConnectHandler),
                                        ('/api/soundcloud-connect/followers/max/.*', followers.SoundCloudConnectMaxFollowersHandler),
                                        ('/api/soundcloud-connect/followings/max/.*', followings.SoundCloudConnectMaxFollowingsHandler),
                                        ('/api/soundcloud-connect/followers/.*', followers.SoundCloudConnectFollowersHandler),
                                        ('/api/soundcloud-connect/followings/.*', followings.SoundCloudConnectFollowingsHandler),                                        
                                        ('/api/soundcloud-connect/favorites/.*', favorites.SoundCloudConnectFavoritesHandler),                                                                                
                                        ('/api/locations.*', locations.LocationsHandler)], debug=util.in_development_enviroment())
  run_wsgi_app(application)

if __name__ == '__main__':
  main()
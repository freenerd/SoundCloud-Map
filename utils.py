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

import os

genres = {}
genres.update({'house': ['house', 'tech house', 'deep house', 'progressive house', 'tech-house', \
							 					 'electro house', 'techhouse', 'minimal house', 'minimal-house' 'funky house', 'dance']}) 
genres.update({'techno': ['techno', 'techno minimal', 'minimal techno', 'minimal-techno']})														
genres.update({'dubstep': ['dubstep', 'dub step']})
genres.update({'hiphop': ['hip hop', 'hip-hop', 'hiphop', 'rap', 'r&b', 'rnb', 'r\'n\'b']})
genres.update({'electronic': ['electronic', 'electro', 'electronica', 'minimal', 'idm']})
genres.update({'drumandbass': ['drum & bass', 'drum and bass', 'drum n bass', 'dnb', 'drum\'n\'bass', 'breakbeat', 'drum&bass', 'breaks']})
genres.update({'trance': ['trance', 'progressive_trance', 'progessive trance', 'psy trance', 'goa']})
genres.update({'rock': ['rock']})
genres.update({'indie': ['indie', 'alternative', 'acoustic']})
genres.update({'pop': ['pop']})
genres.update({'ambient': ['ambient']})
genres.update({'jazz': ['jazz', 'free jazz', 'nu-jazz', 'nu jazz', 'swing']})
genres.update({'classical': ['classical', 'classic']})

top_cities = ['Berlin', 'Paris', 'London', 'New York', 'Los Angeles', 'Tokyo', 'Stockholm', 'Barcelona', 'Istanbul', 'Manchester', 'Hamburg', 'Seattle', 'Miami']

def in_development_enviroment():
	return os.environ["SERVER_SOFTWARE"] != "Google Apphosting/1.0"
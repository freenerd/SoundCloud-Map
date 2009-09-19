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

genre_house = ['house', 'tech house', 'deep house', 'progressive house', 'tech-house', \
							 'electro house', 'techhouse', 'minimal house', 'funky house', 'dance']
genre_techno = ['techno', 'techno minimal', 'minimal techno']
genre_dubstep = ['dubstep', 'dub step']
genre_hiphop = ['hip hop', 'hip-hop', 'hiphop', 'rap', 'r&b']
genre_electronic = ['electronic', 'electro', 'electronica', 'minimal', 'idm']
genre_drumandbass = ['drum & bass', 'drum and bass', 'drum n bass', 'dnb', 'drum\'n\'bass', 'breakbeat', 'drum&bass', 'breaks']   
genre_trance = ['trance', 'progressive_trance']
genre_rock = ['rock']
genre_indie = ['indie', 'alternative', 'acoustic']
genre_pop = ['pop']
genre_ambient = ['ambient']
genre_jazz = ['jazz', 'free jazz', 'nu-jazz', 'nu jazz']
genre_classical = ['classical', 'classic']


def in_development_enviroment():
	return os.environ["SERVER_SOFTWARE"] != "Google Apphosting/1.0"
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

from google.appengine.api.urlfetch_errors import DownloadError
from google.appengine.api import urlfetch
import logging

import utils 
import settings

def main():
  """
  This method makes some queries against the own application api, during which the Memcache is hopefully going to be filled again.
  This should be called by a cronjob every 3 minutes ...
  """

  # Fetch API Locations with Genres
  genre_dict = utils.genres
  genre_dict.update({'all' : ''})
  counter = -1
  queries = []                                                                              
  for genre in  genre_dict.keys():
    counter += 1
    queries.insert(counter, urlfetch.create_rpc())
    urlfetch.make_fetch_call(queries[counter], settings.APPLICATION_URL + "/api/locations/maxtracks?genre=" + genre)
    for i in range(0,20):
      counter += 1
      #logging.info("Genre %s Counter %i i %i" % (genre, counter, i))      
      queries.insert(counter, urlfetch.create_rpc())
      urlfetch.make_fetch_call(queries[counter], settings.APPLICATION_URL + "/api/locations/?&limit=10&offset=%i&genre=%s" % (i, genre))
  
  # Fetch top Cities
  # TODO

  counter2 = 0
  for query in queries:
    #logging.info("waiting for counter "+str(counter2))
    counter2 += 1
    query.wait()
			
if __name__ == '__main__':
  main()
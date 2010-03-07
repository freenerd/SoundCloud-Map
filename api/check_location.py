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
from google.appengine.ext import webapp
from google.appengine.api import memcache
from django.utils import simplejson as json

import util
import settings
import models

from backend.utils import get_location
from api.utils import error_response



class CheckLocationHandler(webapp.RequestHandler):
  """
    Testing this against Google Maps API and see 
    if we can work with the provided info
  """
  
  def get(self):

    # TODO: check if query string params are there
    city = self.request.get('city')     
    country = self.request.get('country')     

    try:
      result = get_location(city, country)
      del result['location']
      self.response.out.write(json.dumps(result))      
    except RuntimeError:
      error_response(self,
                     "NotLocalizable",
                     "Google Maps can not find city %s and country %s" %
                     (city, country))
      return
    except DownloadError:
      error_response(self,
                     "APIError",
                     "Google Maps API is having problems")
      return      
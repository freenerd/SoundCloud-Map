#!/usr/bin/env python

# Copyright (c) 2010 Johan Uhle
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

import models
import scapi
import settings

def get_api_root(soundcloudconnect_user=None):
  if not soundcloudconnect_user:
    raise RuntimeError("Error: get_api_root() has been called without soundcloudconnect_user")
  oauth_authenticator = scapi.authentication.OAuthAuthenticator( \
                                            settings.OAUTH_CONSUMER_KEY,
                                            settings.OAUTH_CONSUMER_SECRET,
                                            soundcloudconnect_user.token,
                                            soundcloudconnect_user.secret)
  return scapi.Scope(scapi.ApiConnector(host=settings.SOUNDCLOUD_API_URL,
                                        authenticator=oauth_authenticator))
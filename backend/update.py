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

from google.appengine.runtime import DeadlineExceededError
from google.appengine.api.labs import taskqueue
import logging
import os
import datetime

import backend.utils 

def main():
  """
  This method adds a task to the task queue intended to querie the SoundCloud API, 
  fetch the latest tracks having been uploaded since the last backend update,
  and adds them to the task queue for further processing.
  It is intended to be called by a cronjob on a short basis, like every 3 minutes.
  """
  try:
    logging.info("Backend update started")
    
    time_from = backend.utils.calculate_time_from()
    time_to = datetime.datetime.now().isoformat()
    
    taskqueue.add(url='/backend-update-task',
                  params={'time_from': time_from, 'time_to': time_to})
                  
    logging.info("Added backend update task to task queue. time_from: %s time_to: %s" % \
                (time_from, time_to))               
        
  except DeadlineExceededError:
    logging.warning("Backend Update has been canceled due to Deadline Exceeded")
    for name in os.environ.keys():
      logging.info("%s = %s" % (name, os.environ[name]))
      
if __name__ == '__main__':
  main()
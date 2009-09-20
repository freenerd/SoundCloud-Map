import settings_private

# API
GOOGLE_MAPS_API_KEY = settings_private.GOOGLE_MAPS_API_KEY
API_RETRIES = 10
SOUNDCLOUD_API_URL = "http://api.soundcloud.com"
SOUNDCLOUD_TIMEZONE_ADJUSTMENT = 0 # in hours behind server timezone

# How many tracks shall be displayed in FrontEnd?
FRONTEND_TRACKS_LIMIT = 200

# How old shall the oldest track in the cache be?
CLEANUP_INTERVAL = 1440 # in minutes

# In which Interval the backend scripts /backend-update is called
API_QUERY_INTERVAL = 15 # in minutes


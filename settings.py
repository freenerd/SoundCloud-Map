import settings_private

APPLICATION_URL = "http://www.tracksonamap.com"

# API
GOOGLE_MAPS_API_KEY = settings_private.GOOGLE_MAPS_API_KEY
GOOGLE_MAPS_API_URL = "http://maps.google.com/maps/geo?key=" + GOOGLE_MAPS_API_KEY
API_RETRIES = 10
SOUNDCLOUD_API_URL = "http://api.soundcloud.com"
SOUNDCLOUD_TIMEZONE_ADJUSTMENT = 0 # in hours behind server timezone
DURATION_LIMIT = "1200000" # in milliseconds to filter out dj-sets + podcasts

# Frontend
FRONTEND_LOCATIONS_LIMIT = 200 # How many locations shall be displayed as default in FrontEnd?
MAX_TRACKS_CACHE_TIME = 30 # How long in minutes are the max tracks counters going to be cached?
                                        
# Backend
# CLEANUP_INTERVAL = 1440 # How old in minutes shall the oldest track in the cache be?
API_QUERY_INTERVAL = 3 # In which Interval in minutes is the backend scripts /backend-update called?
TRACK_BACKEND_UPDATE_LIFETIME = 60 # How long in minutes shall a track remain in Taskqueue/Memcache before purged if not copmpleted?


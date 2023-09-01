from os import environ as os_environ

SOURCE_DRIVE = "D:"                 # Source toggle_RD drive path
DEST_ROOT = "E:\\Kodi"              # Destination cloud drive path
FOLDER_CHECK_FREQUENCY = 2 * 60     # Frequency in seconds
RENEW_ALL_LINKS_AT = 4              # Daily hour when all links are renewed - 24 hours
_RD_API_KEY = ''                    # Real-debrid API Key
_TMDB_API_KEY = ''                  # TMDB API Key
_FANARTTV_API_KEY = ''              # Not necessary
_TRAKT_API_KEY = ''                 # Not necessary

def set_environment_variables():
    os_environ['TMDB_API_KEY']      = _TMDB_API_KEY
    os_environ['FANARTTV_API_KEY']  = _FANARTTV_API_KEY
    os_environ['TRAKT_API_KEY']     = _TRAKT_API_KEY
from os import environ as os_environ

SOURCE_DRIVE                = "D:"                 # Source toggle_RD drive path
DEST_ROOT                   = "E:\\Kodi"           # Destination cloud drive path
CORRECTIONS_FILE_LOCATION   = r""                  # corrections.csv file containing correct TMDB ID, movie/tv type and rcloneRD folder name
FOLDER_CHECK_FREQUENCY      = 2 * 60               # Frequency in seconds
RESET_COUNTER               = 6 * 60 * 60          # After how many hours should the cloud library be reset?
_RD_API_KEY                 = ''                   # Real-debrid API Key
_TMDB_API_KEY               = ''                   # TMDB API Key
_FANARTTV_API_KEY           = ''                   # Not necessary
_TRAKT_API_KEY              = ''                   # Not necessary

def set_environment_variables():
    os_environ['TMDB_API_KEY']      = _TMDB_API_KEY
    os_environ['FANARTTV_API_KEY']  = _FANARTTV_API_KEY
    os_environ['TRAKT_API_KEY']     = _TRAKT_API_KEY
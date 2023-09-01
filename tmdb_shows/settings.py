# -*- coding: UTF-8 -*-
#
# Copyright (C) 2020, Team Kodi
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
# pylint: disable=missing-docstring

from os import environ as os_environ
import json
import sys
import urllib.parse
from . import api_utils
from datetime import datetime, timedelta


def _get_date_numeric(datetime_):
    return (datetime_ - datetime(1970, 1, 1)).total_seconds()


def _get_configuration():
    return api_utils.load_info('https://api.themoviedb.org/3/configuration', params={'api_key': TMDB_CLOWNCAR}, verboselog=VERBOSELOG)


def _load_base_urls():
    image_root_url = None
    preview_root_url = None
    last_updated = False
    if not image_root_url or not preview_root_url or not last_updated or float(last_updated) < _get_date_numeric(datetime.now() - timedelta(days=30)):
        conf = _get_configuration()
        if conf:
            image_root_url = conf['images']['secure_base_url'] + 'original'
            preview_root_url = conf['images']['secure_base_url'] + 'w780'
            last_updated = str(_get_date_numeric(datetime.now()))
    return image_root_url, preview_root_url


TMDB_CLOWNCAR = os_environ['TMDB_API_KEY']
FANARTTV_CLOWNCAR = os_environ['FANARTTV_API_KEY']
TRAKT_CLOWNCAR = os_environ['TRAKT_API_KEY']
MAXIMAGES = 200
FANARTTV_MAPPING = {'showbackground': 'backdrops',
                    'tvposter': 'posters',
                    'tvbanner': 'banner',
                    'hdtvlogo': 'clearlogo',
                    'clearlogo': 'clearlogo',
                    'hdclearart': 'clearart',
                    'clearart': 'clearart',
                    'tvthumb': 'landscape',
                    'characterart': 'characterart',
                    'seasonposter': 'seasonposters',
                    'seasonbanner': 'seasonbanner',
                    'seasonthumb': 'seasonlandscape'
                    }

# try:
#     source_params = dict(urllib.parse.parse_qsl(sys.argv[2]))
# except IndexError:
source_params = {}
source_settings = json.loads(source_params.get('pathSettings', '{}'))

KEEPTITLE = source_settings.get('keeporiginaltitle', False)
CATLANDSCAPE = source_settings.get('cat_landscape', True)
STUDIOCOUNTRY = source_settings.get('studio_country', False)
ENABTRAILER = source_settings.get('enab_trailer', False)
PLAYERSOPT = source_settings.get('players_opt', "").lower()
VERBOSELOG = source_settings.get('verboselog', False)
LANG = source_settings.get('language', "en-US")
CERT_COUNTRY = source_settings.get('tmdbcertcountry', "en-US").lower()
IMAGEROOTURL, PREVIEWROOTURL = _load_base_urls()

if source_settings.get('usecertprefix', False):
    CERT_PREFIX = source_settings.get('certprefix', '')
else:
    CERT_PREFIX = ''
primary_rating = source_settings.get('ratings', 'imdb').lower()
RATING_TYPES = [primary_rating]
if source_settings.get('imdbanyway', True) and primary_rating != 'imdb':
    RATING_TYPES.append('imdb')
if source_settings.get('traktanyway', False) and primary_rating != 'trakt':
    RATING_TYPES.append('trakt')
if source_settings.get('tmdbanyway', True) and primary_rating != 'tmdb':
    RATING_TYPES.append('tmdb')
FANARTTV_ENABLE = source_settings.get(
    'enable_fanarttv', False)
FANARTTV_CLIENTKEY = source_settings.get(
    'fanarttv_clientkey', '')

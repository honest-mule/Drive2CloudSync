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

"""Functions to interact with TMDb API."""
from os import environ as os_environ
from . import api_utils


HEADERS = (
    ('User-Agent', 'Kodi Movie scraper by Team Kodi'),
    ('Accept', 'application/json'),
)
api_utils.set_headers(dict(HEADERS))

TMDB_PARAMS = {'api_key': os_environ['TMDB_API_KEY'] }
BASE_URL = 'https://api.themoviedb.org/3/{}'
SEARCH_URL = BASE_URL.format('search/movie')
FIND_URL = BASE_URL.format('find/{}')
MOVIE_URL = BASE_URL.format('movie/{}')
COLLECTION_URL = BASE_URL.format('collection/{}')
CONFIG_URL = BASE_URL.format('configuration')


def search_movie(query, year=None, language=None):
    # type: (Text) -> List[InfoType]
    """
    Search for a movie

    :param title: movie title to search
    :param year: the year to search (optional)
    :param language: the language filter for TMDb (optional)
    :return: a list with found movies
    """
    theurl = SEARCH_URL
    params = _set_params(None, language)
    params['query'] = query
    if year is not None:
        params['year'] = str(year)
    return api_utils.load_info(theurl, params=params)


def find_movie_by_external_id(external_id, language=None):
    # type: (Text) -> List[InfoType]
    """
    Find movie based on external ID

    :param mid: external ID
    :param language: the language filter for TMDb (optional)
    :return: the movie or error
    """
    theurl = FIND_URL.format(external_id)
    params = _set_params(None, language)
    params['external_source'] = 'imdb_id'
    return api_utils.load_info(theurl, params=params)



def get_movie(mid, language=None, append_to_response=None):
    # type: (Text) -> List[InfoType]
    """
    Get movie details

    :param mid: TMDb movie ID
    :param language: the language filter for TMDb (optional)
    :append_to_response: the additional data to get from TMDb (optional)
    :return: the movie or error
    """
    theurl = MOVIE_URL.format(mid)
    return api_utils.load_info(theurl, params=_set_params(append_to_response, language))


def get_collection(collection_id, language=None, append_to_response=None):
    # type: (Text) -> List[InfoType]
    """
    Get movie collection information

    :param collection_id: TMDb collection ID
    :param language: the language filter for TMDb (optional)
    :append_to_response: the additional data to get from TMDb (optional)
    :return: the movie or error
    """
    theurl = COLLECTION_URL.format(collection_id)
    return api_utils.load_info(theurl, params=_set_params(append_to_response, language))


def get_configuration():
    # type: (Text) -> List[InfoType]
    """
    Get configuration information

    :return: configuration details or error
    """
    return api_utils.load_info(CONFIG_URL, params=TMDB_PARAMS.copy())


def _set_params(append_to_response, language):
    params = TMDB_PARAMS.copy()
    img_lang = 'en,null'
    if language is not None:
        params['language'] = language
        img_lang = '%s,en,null' % language[0:2]
    if append_to_response is not None:
        params['append_to_response'] = append_to_response
        if 'images' in append_to_response:
            params['include_image_language'] = img_lang
    return params

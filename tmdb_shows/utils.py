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

"""Misc utils"""

from __future__ import absolute_import, unicode_literals


try:
    from typing import Text, Optional, Any, Dict  # pylint: disable=unused-import
except ImportError:
    pass

ADDON_ID = 'metadata.tvshows.themoviedb.org.python'


class logger:
    log_message_prefix = ""

    @staticmethod
    def log(message, level=None):
        # type: (Text, int) -> None
        # if isinstance(message, bytes):
        #     message = message.decode('utf-8')
        # message = logger.log_message_prefix + message
        # xbmc.log(message, level)
        pass

    @staticmethod
    def info(message):
        # type: (Text) -> None
        # logger.log(message, xbmc.LOGINFO)
        pass

    @staticmethod
    def error(message):
        # type: (Text) -> None
        # logger.log(message, xbmc.LOGERROR)
        pass

    @staticmethod
    def debug(message):
        # type: (Text) -> None
        # logger.log(message, xbmc.LOGDEBUG)
        pass


def safe_get(dct, key, default=None):
    # type: (Dict[Text, Any], Text, Any) -> Any
    """
    Get a key from dict

    Returns the respective value or default if key is missing or the value is None.
    """
    if key in dct and dct[key] is not None:
        return dct[key]
    return default

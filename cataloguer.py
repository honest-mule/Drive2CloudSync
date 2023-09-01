from settings import *
set_environment_variables()

import os
import re
from time import time, sleep
from pathlib import Path
import datetime
from rd_api import *
from cache import Cache
from tmdb_movies.tmdb import TMDBMovieScraper
from tmdb_shows.tmdb import search_show, load_show_info
from utils import sanitise_title_for_windows_folder_name, get_movie_info_from_torrent_name, get_show_info_from_torrent_name
import logging
import traceback
from thefuzz import fuzz


# --- LOGGING SETUP START --- #

# logging.basicConfig(level=logging.INFO, file='status.log')

# Gets or creates a logger
logger = logging.getLogger(__name__)  

# set log level
logger.setLevel(logging.INFO)

# define file handler and set formatter
file_handler = logging.FileHandler('status.log')
formatter    = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s')
file_handler.setFormatter(formatter)

# add file handler to logger
logger.addHandler(file_handler)

# --- LOGGING SETUP END --- #

cache = Cache()
movie_scraper = TMDBMovieScraper(None, None, None)

SEVEN_DAYS = 7 * 24 * 60 * 60

def movies(folder_name, torrents, tmdb_info = None):
    torrent = None
    if isinstance(torrents, list):
        for _t in torrents:
            if _t["filename"] != folder_name:
                continue
            torrent = _t
            break
    else:
        torrent = torrents
    if not torrent:
        torrent_id = cache.get_torrent_id(folder_name)
        if not torrent_id:
            logger.warning(f"Skipping movies\{folder_name} since respective torrent_id could not be found")
            return
        torrent = get_torrent_info(torrent_id)
    if torrent["status"] != "downloaded":
        return
    
    new_folder_name = cache.get_dest_folder(torrent["id"])

    if not new_folder_name:
        if not tmdb_info:
            cache_record = cache.fetch(torrent["id"])
            if not cache_record:
                [title, year] = get_movie_info_from_torrent_name(folder_name)
                tmdb_info = movie_scraper.search(title, year)
                if len(tmdb_info) == 0:
                    logger.warning(f"Skipping movies\{folder_name} since TMDB returned 0 results")
                    return
                else:
                    max_similarity_ratio = 0
                    _tmdb_info = None
                    for _mv_info in tmdb_info:
                        sim_ratio = fuzz.ratio(title, _mv_info["title"])
                        if sim_ratio == 100:
                            _tmdb_info = _mv_info
                            break
                        if sim_ratio > max_similarity_ratio:
                            max_similarity_ratio = sim_ratio
                            _tmdb_info = _mv_info
                    tmdb_info = _tmdb_info
                    logger.info(f"Found best match for {folder_name} -\n\tTMDB_ID: {tmdb_info['id']}\n\tTitle: {tmdb_info['title']}\n\tOG title: {tmdb_info['original_title']}")
                cache.save(torrent["id"], "movie", tmdb_info["id"], folder_name)
                cache_record = cache.fetch(torrent["id"])
            else:
                tmdb_info = movie_scraper.get_details({"tmdb": cache_record.tmdb_id})["info"]
                tmdb_info["release_date"] = tmdb_info["premiered"]    
        new_folder_name = f"{tmdb_info['title']} ({tmdb_info['release_date'][:4]})"
        new_folder_name = sanitise_title_for_windows_folder_name(new_folder_name)
        cache.save_dest_folder(torrent["id"], new_folder_name)

    new_folder_path = os.path.join(os.sep, DEST_ROOT + os.sep, "movies", new_folder_name)
    os.makedirs(new_folder_path, exist_ok=True)

    torrent_info = get_torrent_info(torrent['id'])
    selected_files = [x for x in torrent_info['files'] if x['selected']]
    for file_info, file_uri in zip(selected_files, torrent_info['links']):
        direct_link = get_direct_link(file_uri)
        if(direct_link.endswith(".rar")):
            logger.warning(f"RD sent .rar for {torrent_info['filename']}{file_info['path']}")
            continue

        strm_dirs = file_info['path'].split("/")[1:]
        strm_file_name = strm_dirs.pop()
        strm_path = Path(new_folder_path, *strm_dirs, f"{strm_file_name}.strm")
        strm_path.parent.mkdir(parents=True, exist_ok=True)

        if os.path.isfile(strm_path):
            last_modified = os.path.getmtime(strm_path)
            if time() < last_modified + SEVEN_DAYS:
                continue
        with open(strm_path, "w") as strm_file:
            strm_file.write(direct_link)

def shows(folder_name, torrents, tmdb_info = None):
    torrent = None
    if isinstance(torrents, list):
        for _t in torrents:
            if _t["filename"] != folder_name:
                continue
            torrent = _t
            break
    else:
        torrent = torrents
    if not torrent:
        torrent_id = cache.get_torrent_id(folder_name)
        if not torrent_id:
            logger.warning(f"Skipping shows\{folder_name} since respective torrent_id could not be found")
            return
        torrent = get_torrent_info(torrent_id)
    if torrent["status"] != "downloaded":
        return
    
    new_folder_name = cache.get_dest_folder(torrent["id"])

    og_season = 1
    if not new_folder_name or new_folder_name:
        if not tmdb_info:
            cache_record = cache.fetch(torrent["id"])
            if not cache_record:
                [title, year, og_season, _] = get_show_info_from_torrent_name(folder_name)
                tmdb_info = search_show(title, year)
                if len(tmdb_info) == 0:
                    logger.warning(f"Skipping shows\{folder_name} since TMDB returned 0 results")
                    return
                else:
                    max_similarity_ratio = 0
                    _tmdb_info = None
                    for _shw_info in tmdb_info:
                        sim_ratio = fuzz.ratio(title, _shw_info["name"])
                        if sim_ratio == 100:
                            _tmdb_info = _shw_info
                            break
                        if sim_ratio > max_similarity_ratio:
                            max_similarity_ratio = sim_ratio
                            _tmdb_info = _shw_info
                    tmdb_info = _tmdb_info
                cache.save(torrent["id"], "tv", tmdb_info["id"], folder_name)
                cache_record = cache.fetch(torrent["id"])
            else:
                tmdb_info = load_show_info(cache_record.tmdb_id)
        new_folder_name = f"{tmdb_info['name']} ({tmdb_info['first_air_date'][:4]})"
        new_folder_name = sanitise_title_for_windows_folder_name(new_folder_name)
        cache.save_dest_folder(torrent["id"], new_folder_name)

    new_folder_path = os.path.join(os.sep, DEST_ROOT + os.sep, "shows", new_folder_name)
    os.makedirs(new_folder_path, exist_ok=True)

    torrent_info = get_torrent_info(torrent['id'])
    selected_files = [x for x in torrent_info['files'] if x['selected']]
    ep_counter = 0
    for file_info, file_uri in zip(selected_files, torrent_info['links']):
        direct_link = get_direct_link(file_uri)
        if(direct_link.endswith(".rar")):
            logger.warning(f"RD sent .rar for {torrent_info['filename']}{file_info['path']}")
            continue

        ep_counter = ep_counter + 1
        strm_dirs = file_info['path'].split("/")[1:]
        strm_file_name: str = strm_dirs.pop()
        [_x, _y, season, episodes] = get_show_info_from_torrent_name(strm_file_name)

        if not season and not og_season:
            season = 1
        elif not season and og_season:
            season = og_season

        strm_path = os.path.join(new_folder_path, f"Season {season}", f"{new_folder_name} S{season:02d}")

        if len(episodes) > 0:
            for ep_no in episodes:
                strm_path = f"{strm_path}E{ep_no:02d}"
            strm_path = Path(f"{strm_path}.strm")
        else:
            episode_number = re.search(r"(\d+)", strm_file_name)
            if episode_number:
                episode_number = int(episode_number.groups()[0])
                strm_path = f"{strm_path}E{episode_number:02d}"
                strm_path = Path(f"{strm_path}.strm")
            else:
                strm_path = Path(new_folder_path, *strm_dirs, f"{strm_file_name}.strm")

        strm_path.parent.mkdir(parents=True, exist_ok=True)

        if os.path.isfile(strm_path):
            last_modified = os.path.getmtime(strm_path)
            if time() < last_modified + SEVEN_DAYS:
                continue
        with open(strm_path, "w") as strm_file:
            strm_file.write(direct_link)

def unknown(folder_name, torrents):
    torrent = None
    for _t in torrents:
        if _t["filename"] != folder_name:   
            continue
        torrent = _t
        break
    if torrent["status"] != "downloaded":
        return
    if not torrent:
        logger.warning(f"Skipping default\{folder_name} since respective torrent_id could not be found")
    cache_record = cache.fetch(torrent["id"])
    if not cache_record:
        logger.warning(f"Skipping default\{folder_name} since it's an unknown entity")
        return
    if cache_record.type == "movie":
        return movies(folder_name, torrent)
    elif cache_record.type == "tv":
        return shows(folder_name, torrent)
    
def error_string(ex: Exception) -> str:
    return '\n'.join([
        ''.join(traceback.format_exception_only(None, ex)).strip(),
        ''.join(traceback.format_exception(None, ex, ex.__traceback__)).strip()
    ])
    
def try_folder_resolution(type, folder_name, torrents):
    try:
        if type == 'movie':
            movies(folder_name, torrents)
        elif type == 'show':
            shows(folder_name, torrents)
        else:
            unknown(folder_name, torrents)
    except Exception as ex:
        ex_string = error_string(ex)
        ex_string = ex_string.replace("\n", "\n\t")
        logger.error(f"{type}\{folder_name} could not be resolved\n\tDetails: {ex_string}")

seconds_passed = 0
SECONDS_IN_A_DAY = 24 * 60 * 60

if __name__ == "__main__":
    torrents = get_torrents()
    movies_path = os.path.join(os.sep, SOURCE_DRIVE + os.sep, "movies")
    shows_path = os.path.join(os.sep, SOURCE_DRIVE + os.sep, "shows")
    uncategorized_path = os.path.join(os.sep, SOURCE_DRIVE + os.sep, "default")

    categories_to_resolve = [
        {
            "type": "movie",
            "path": movies_path,
            "dirs": []
        },
        {
            "type": "show",
            "path": shows_path,
            "dirs": []
        },
        {
            "type": "unknown",
            "path": uncategorized_path,
            "dirs": []
        }
    ]

    for category in categories_to_resolve:
        category["dirs"] = os.listdir(category["path"])
        for folder_name in category["dirs"]:
            try_folder_resolution(category["type"], folder_name, torrents)
    
    once_a_day_run_complete = True

    sleep(5 * 60)
    seconds_passed = 5 * 60

    while True:
        torrents = get_torrents()

        if seconds_passed > SECONDS_IN_A_DAY and datetime.datetime.now().hour() > RENEW_ALL_LINKS_AT:
            for category in categories_to_resolve:
                category["dirs"] = os.listdir(category["path"])
                for folder_name in category["dirs"]:
                    try_folder_resolution(category["type"], folder_name, torrents)
            seconds_passed = 0
        else:
            for category in categories_to_resolve:
                _folders_list = os.listdir(category["path"])
                if len(_folders_list) > len(category["dirs"]):
                    new_dirs = [x for x in _folders_list if x not in category["dirs"]]
                    for folder_name in new_dirs:
                        try_folder_resolution(category["type"], folder_name, torrents)
                category["dirs"] = _folders_list
        
        sleep(FOLDER_CHECK_FREQUENCY)
        seconds_passed = seconds_passed + FOLDER_CHECK_FREQUENCY

        
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
from utils import *
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
file_handler = logging.FileHandler('status.log', "a+", "utf-8")
formatter    = logging.Formatter(u'%(asctime)s : %(levelname)s : %(name)s : %(message)s')
file_handler.setFormatter(formatter)

# add file handler to logger
logger.addHandler(file_handler)

# --- LOGGING SETUP END --- #

cache = Cache(logger)
movie_scraper = TMDBMovieScraper(None, None, None)

SEVEN_DAYS = 7 * 24 * 60 * 60

def movies(folder_name, torrents, tmdb_info = None):
    torrent = None
    if isinstance(torrents, dict):
        if "id" in torrents:
            torrent = torrents
        elif folder_name in torrents:
            torrent = torrents[folder_name]
    if not torrent:
        torrent_id = cache.get_torrent_id(folder_name)
        if not torrent_id:
            logger.warning(f"Skipping movies\{folder_name} since respective torrent_id could not be found")
            return
        torrent = get_torrent_info(torrent_id)
        if not torrent:
            logger.warning(f"Skipping movies\{folder_name} since Real-Debrid API returned without relevant torrent info")
            return
    if torrent["status"] != "downloaded":
        return
    
    new_folder_name = cache.get_dest_folder(torrent["id"])
    if not new_folder_name:
        new_folder_name = cache.get_dest_folder2(folder_name)
        if new_folder_name:
            cache.update_torrent_id(torrent["id"])

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
                    tmdb_info = _tmdb_info if _tmdb_info else tmdb_info[0]
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

    if "files" in torrent:
        torrent_info = torrent
    else:
        torrent_info = get_torrent_info(torrent["id"])
        if not torrent_info:
            logger.warning(f"Skipping movies\{folder_name} since Real-Debrid API returned without relevant torrent info")
            return
    selected_files = [x for x in torrent_info['files'] if x['selected']]
    for file_info, file_uri in zip(selected_files, torrent_info['links']):
        direct_link = get_direct_link(file_uri)
        if(direct_link.endswith(".rar")):
            logger.warning(f"RD sent .rar for {torrent_info['filename']}{file_info['path']}")
            continue

        strm_dirs = file_info['path'].split("/")[1:]
        strm_file_name = strm_dirs.pop()
        if len(strm_dirs) > 0:
            for idx, _dir in enumerate(strm_dirs):
                if re.search("^(featurettes|extras)", _dir, re.RegexFlag.IGNORECASE):
                    strm_dirs = strm_dirs[idx+1:]
                    break
            strm_path = Path(new_folder_path, "Extras", *strm_dirs, f"{strm_file_name}.strm")
        else:
            strm_path = Path(new_folder_path, f"{strm_file_name}.strm")
        strm_path.parent.mkdir(parents=True, exist_ok=True)

        os.remove(strm_path)
        with open(strm_path, "w") as strm_file:
            strm_file.write(direct_link)
        logger.info(f"Created:\n\tStream path: {strm_path}\n\tDirect link: {direct_link}")

def shows(folder_name, torrent = None, tmdb_info = None):
    torrent = None
    if isinstance(torrents, dict):
        if "id" in torrents:
            torrent = torrents
        elif folder_name in torrents:
            torrent = torrents[folder_name]
    if not torrent:
        torrent_id = cache.get_torrent_id(folder_name)
        if not torrent_id:
            logger.warning(f"Skipping shows\{folder_name} since respective torrent_id could not be found")
            return
        torrent = get_torrent_info(torrent_id)
        if not torrent:
            logger.warning(f"Skipping movies\{folder_name} since Real-Debrid API returned without relevant torrent info")
            return
    if torrent["status"] != "downloaded":
        return
    
    [title, year, season_number_in_root, _] = get_show_info_from_torrent_name(folder_name)
    new_folder_name = cache.get_dest_folder(torrent["id"])
    if not new_folder_name:
        new_folder_name = cache.get_dest_folder2(folder_name)
        if new_folder_name:
            cache.update_torrent_id(torrent["id"])
    
    if not new_folder_name:
        if not tmdb_info:
            cache_record = cache.fetch(torrent["id"])
            if not cache_record:
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

    if "files" in torrent:
        torrent_info = torrent
    else:
        torrent_info = get_torrent_info(torrent['id'])
        if not torrent_info:
            logger.warning(f"Skipping movies\{folder_name} since Real-Debrid API returned without relevant torrent info")
            return
    selected_files = [x for x in torrent_info['files'] if x['selected']]
    ep_counter = 0
    for file_info, file_uri in zip(selected_files, torrent_info['links']):
        direct_link = get_direct_link(file_uri)
        if(direct_link.endswith(".rar")):
            logger.warning(f"RD sent .rar for {torrent_info['filename']}{file_info['path']}")
            continue

        ep_counter = ep_counter + 1
        strm_dirs: list = file_info['path'].split("/")[1:]
        strm_file_name: str = strm_dirs.pop()
        [_x, _y, season, episodes] = get_show_info_from_torrent_name(strm_file_name)

        if not season:
            for _dir in reversed(strm_dirs):
                [_x, _y, _season, _z] = get_show_info_from_torrent_name(_dir)
                if _season:
                    season = _season
                    break

        # Since no season info could be found for the TV show -
        # we'll assume the content belongs to Season 1
        if not season and not season_number_in_root:
            season = 1
        elif not season:
            season = season_number_in_root

        if any(re.search("^featurettes|extras$", _dir, re.RegexFlag.IGNORECASE) for _dir in strm_dirs):
            strm_path = Path(new_folder_path, f"Season {season}", "Extras", f"{strm_file_name}.strm")
        elif len(episodes) > 0:
            if any(re.search("^specials$", _dir, re.RegexFlag.IGNORECASE) for _dir in strm_dirs):
                strm_path = os.path.join(new_folder_path, "Season 00", f"{new_folder_name} S00")
            else:
                strm_path = os.path.join(new_folder_path, f"Season {season}", f"{new_folder_name} S{season:02d}")
            for ep_no in episodes:
                strm_path = f"{strm_path}E{ep_no:02d}"
            strm_path = Path(f"{strm_path}.strm")
        else:
            # Possible strategy when episode names are without E** formatting
            # episode_number = re.search(r"(\d+)", strm_file_name)
            # if episode_number:
            #     episode_number = int(episode_number.groups()[0])
            #     strm_path = f"{strm_path}E{episode_number:02d}"
            #     strm_path = Path(f"{strm_path}.strm")
            # else:
            if len(strm_dirs) > 0:
                if any(re.search("^specials$", _dir, re.RegexFlag.IGNORECASE) for _dir in strm_dirs):
                    strm_path = Path(new_folder_path, f"Season 00", f"{strm_file_name}.strm")
                else:    
                    for idx, _dir in enumerate(strm_dirs):
                        if re.search("^(season|series|featurettes|extras)", _dir, re.RegexFlag.IGNORECASE):
                            strm_dirs = strm_dirs[idx+1:]
                            break
                    strm_path = Path(new_folder_path, f"Season {season}", "Extras", *strm_dirs, f"{strm_file_name}.strm")
            else:
                # Here we're assuming the file is possibly a badly marked episode
                strm_path = Path(new_folder_path, f"Season {season}", f"{strm_file_name}.strm")

        strm_path.parent.mkdir(parents=True, exist_ok=True)
        
        os.remove(strm_path)
        with open(strm_path, "w") as strm_file:
            strm_file.write(direct_link)
        logger.info(f"Created:\n\tStream path: {strm_path}\n\tDirect link: {direct_link}")

def unknown(folder_name: str, torrents = None):
    torrent = None
    if isinstance(torrents, dict):
        if "id" in torrents:
            torrent = torrents
        elif folder_name in torrents:
            torrent = torrents[folder_name]
        else:
            logger.warning("Skipping default\{folder_name} since its respective torrent couldn't be found.")
            return False
    cache_record = cache.fetch(torrent["id"])
    if not cache_record:
        _tmp = cache.get_torrent_id(folder_name)
        if _tmp:
            cache.update_torrent_id(torrent["id"], folder_name)
            cache_record = cache.fetch(torrent["id"])
        else:
            logger.warning(f"Skipping default\{folder_name} since its an unknown entity")
            return
    if cache_record.type == "movie":
        return movies(folder_name, torrent)
    elif cache_record.type == "tv":
        return shows(folder_name, torrent)
    
def write_strm_file(strm_path: str, direct_link: str):
    try:
        # Open the file in 'r+' mode, which allows both reading and writing
        with open(strm_path, 'r+') as file:
            old_link = file.read().strip()
            
            # Check if the existing contents match the new contents
            if old_link != direct_link:
                # Contents don't match, so update the file
                file.seek(0)  # Move the file pointer to the beginning
                file.write(direct_link)  # Overwrite the existing contents
                file.truncate()  # Truncate any extra characters if the new contents are shorter
                logger.info(f"Updated:\n\tStream path:{strm_path}\n\tDirect link:{direct_link}")
            else:
                pass
    except FileNotFoundError:
        # The file doesn't exist, so create it with the new contents
        with open(strm_path, 'w') as file:
            file.write(direct_link)
        logger.info(f"Created:\n\tStream path:{strm_path}\n\tDirect link:{direct_link}")
    
def sort_torrents(torrents):
    _dict = {}
    for torrent in torrents:
        if torrent["filename"] in _dict or torrent["status"] != "downloaded":
            continue
        _dict[torrent["filename"]] = torrent
    return _dict
    
def resolve_media_type(folder_name):
    tv_regex = re.compile(r"[\W](S[0-9]{2}|SEASON|COMPLETE|[^457a-z\W\s]-[0-9]+)", re.RegexFlag.IGNORECASE)
    movie_regex = re.compile(r"(19|20)([0-9]{2} ?\.?)")
    if tv_regex.search(folder_name):
        return "tv"
    if movie_regex.search(folder_name):
        return "movie"
    
    return "unknown"
    
def error_string(ex: Exception) -> str:
    return '\n'.join([
        ''.join(traceback.format_exception_only(None, ex)).strip(),
        ''.join(traceback.format_exception(None, ex, ex.__traceback__)).strip()
    ])
    
def try_folder_resolution(type, folder_name, torrents):
    if not torrents:
        logger.error("Empty torrents list. Check internet connection or RD API key.")
        return
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

def manage_corrections(corrections: list[Correction]):
    global CORRECTIONS_FILE_LOCATION
    _corrections: list[Correction] = []
    try:
        if not os.path.isfile(CORRECTIONS_FILE_LOCATION):
            return _corrections
        with open(CORRECTIONS_FILE_LOCATION, "r+") as corrections_file:
            for line in corrections_file.readlines():
                _values = line.split(",")
                correction = Correction(tmdb_id=_values[0].strip(),
                                        type=_values[1].strip(), folder_name=_values[2].strip())
                omit_correction = False
                for former_correction in corrections:
                    if former_correction.folder_name == correction.folder_name and former_correction.done:
                        omit_correction = True
                        break
                if not omit_correction:
                    _corrections.append(correction)
            corrections_file.seek(0)
            corrections_file.truncate()
            for pending in _corrections:
                corrections_file.write(f"{pending.tmdb_id},{pending.type},{pending.folder_name}\n")
    except Exception as ex:
        ex_string = error_string(ex)
        ex_string = ex_string.replace("\n", "\n\t")
        logger.error(f"Unable to load corrections\n\tException Info: {ex_string}")
    finally:
        return _corrections

seconds_passed = 0
SECONDS_IN_A_DAY = 24 * 60 * 60

if __name__ == "__main__":
    torrents = sort_torrents(get_torrents())

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

    corrections: list[Correction] = []
    corrections = manage_corrections(corrections)
    for correction in corrections:
        if not cache.fix_entry(correction):
            continue
        try_folder_resolution(correction.type, correction.folder_name, torrents)
        correction.done = True
    corrections = manage_corrections(corrections)

    for category in categories_to_resolve:
        category["dirs"] = os.listdir(category["path"])
        for folder_name in category["dirs"]:
            try_folder_resolution(category["type"], folder_name, torrents)
    
    sleep(5 * 60)
    seconds_passed = 5 * 60

    while True:
        torrents = sort_torrents(get_torrents())
        
        corrections = manage_corrections(corrections)
        for correction in corrections:
            if not cache.fix_entry(correction):
                continue
            try_folder_resolution(correction.type, correction.folder_name, torrents)
            correction.done = True
        corrections = manage_corrections(corrections)

        if seconds_passed > SECONDS_IN_A_DAY and datetime.datetime.now().hour() > RENEW_ALL_LINKS_AT:
            for category in categories_to_resolve:
                category["dirs"] = os.listdir(category["path"])
                for folder_name in category["dirs"]:
                    try_folder_resolution(category["type"], folder_name, torrents)
            seconds_passed = 0
        else:
            for category in categories_to_resolve:
                _folders_list = [_dir for _dir in os.listdir(category["path"]) if _dir not in category(["dirs"])]
                if len(_folders_list) > len(category["dirs"]):
                    new_dirs = [x for x in _folders_list if x not in category["dirs"]]
                    for folder_name in new_dirs:
                        try_folder_resolution(category["type"], folder_name, torrents)
                category["dirs"] = category["dirs"] + _folders_list
        
        sleep(FOLDER_CHECK_FREQUENCY)
        seconds_passed = seconds_passed + FOLDER_CHECK_FREQUENCY

        
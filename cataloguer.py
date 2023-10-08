from settings import *
set_environment_variables()

import os
import re
from time import time, sleep
from pathlib import Path
import datetime
from dateutil import parser as dt_parser
from rd_api import *
from cache import Cache
from tmdb_movies.tmdb import TMDBMovieScraper
from tmdb_shows.tmdb import search_show, load_show_info
from utils import *
import logging
import traceback
from thefuzz import fuzz
import argparse


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

def movies(torrent, tmdb_info = None):
    if not torrent:
        logger.warning(f"Skipping movies\??? since torrent object is empty")
        return
    
    torrent_info = get_torrent_info(torrent["id"])
    if not torrent_info:
        logger.warning(f"Skipping movies\{torrent['filename']} since Real-Debrid API returned without relevant torrent info")
        return
    if torrent_info["status"] != "downloaded":
        return
    
    new_folder_name = cache.get_dest_folder(torrent["id"])
    if not new_folder_name:
        new_folder_name = cache.get_dest_folder2(torrent["hash"])
        if new_folder_name:
            cache.update_torrent_id(torrent["id"], torrent['hash'])

    if not new_folder_name:
        if not tmdb_info:
            cache_record = cache.fetch(torrent["id"])
            if not cache_record:
                [title, year] = get_movie_info_from_torrent_name(torrent['filename'])
                tmdb_info = movie_scraper.search(title, year)
                if len(tmdb_info) == 0:
                    logger.warning(f"Skipping movies\{torrent['filename']} since TMDB returned 0 results")
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
                    logger.info(f"Found best match for {torrent['filename']} -\n\tTMDB_ID: {tmdb_info['id']}\n\tTitle: {tmdb_info['title']}\n\tOG title: {tmdb_info['original_title']}")
                cache.save(torrent["id"], "movie", tmdb_info["id"], torrent['filename'], torrent["hash"])
                cache_record = cache.fetch(torrent["id"])
            else:
                tmdb_info = movie_scraper.get_details({"tmdb": cache_record.tmdb_id})["info"]
                tmdb_info["release_date"] = tmdb_info["premiered"]    
        new_folder_name = f"{tmdb_info['title']} ({tmdb_info['release_date'][:4]})"
        new_folder_name = sanitise_title_for_windows_folder_name(new_folder_name)
        cache.save_dest_folder(torrent["id"], new_folder_name)

    new_folder_path = os.path.join(os.sep, DEST_ROOT + os.sep, "movies", new_folder_name)
    os.makedirs(new_folder_path, exist_ok=True)

    selected_files = [x for x in torrent_info['files'] if x['selected']]
    for file_info, file_uri in zip(selected_files, torrent_info['links']):
        if file_uri in torrent["direct_links"]:
            direct_link = torrent["direct_links"][file_uri]["download"]
        else:
            direct_link = get_direct_link(file_uri)
            logger.info(f"Direct link generated:\n\tTorrent: {torrent_info['filename']}\n\tPath: {file_info['path']}\n\tLink: {direct_link}")
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

        try:
            os.remove(strm_path)
        except:
            pass
        with open(strm_path, "w") as strm_file:
            strm_file.write(direct_link)
        logger.debug(f"Created:\n\tStream path: {strm_path}\n\tDirect link: {direct_link}")

def shows(torrent, tmdb_info = None):
    if not torrent:
        logger.warning(f"Skipping shows\??? since torrent object is empty")
        return
    
    torrent_info = get_torrent_info(torrent["id"])
    if not torrent_info:
        logger.warning(f"Skipping shows\{torrent['filename']} since Real-Debrid API returned without relevant torrent info")
        return
    if torrent_info["status"] != "downloaded":
        return
    
    [title, year, season_number_in_root, _] = get_show_info_from_torrent_name(torrent['filename'])
    new_folder_name = cache.get_dest_folder(torrent["id"])
    if not new_folder_name:
        new_folder_name = cache.get_dest_folder2(torrent["hash"])
        if new_folder_name:
            cache.update_torrent_id(torrent["id"], torrent['hash'])
    
    if not new_folder_name:
        if not tmdb_info:
            cache_record = cache.fetch(torrent["id"])
            if not cache_record:
                tmdb_info = search_show(title, year)
                if len(tmdb_info) == 0:
                    logger.warning(f"Skipping shows\{torrent['filename']} since TMDB returned 0 results")
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
                cache.save(torrent["id"], "tv", tmdb_info["id"], torrent['filename'], torrent["hash"])
                cache_record = cache.fetch(torrent["id"])
            else:
                tmdb_info = load_show_info(cache_record.tmdb_id)
        new_folder_name = f"{tmdb_info['name']} ({tmdb_info['first_air_date'][:4]})"
        new_folder_name = sanitise_title_for_windows_folder_name(new_folder_name)
        cache.save_dest_folder(torrent["id"], new_folder_name)

    new_folder_path = os.path.join(os.sep, DEST_ROOT + os.sep, "shows", new_folder_name)
    os.makedirs(new_folder_path, exist_ok=True)

    selected_files = [x for x in torrent_info['files'] if x['selected']]
    ep_counter = 0
    for file_info, file_uri in zip(selected_files, torrent_info['links']):
        if file_uri in torrent["direct_links"]:
            direct_link = torrent["direct_links"][file_uri]["download"]
        else:
            direct_link = get_direct_link(file_uri)
            logger.info(f"Direct link generated:\n\tTorrent: {torrent_info['filename']}\n\tPath: {file_info['path']}\n\tLink: {direct_link}")
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
        
        try:
            os.remove(strm_path)
        except:
            pass
        with open(strm_path, "w") as strm_file:
            strm_file.write(direct_link)
        logger.debug(f"Created:\n\tStream path: {strm_path}\n\tDirect link: {direct_link}")

def unknown(torrent = None):
    if not torrent:
        return False
    cache_record = cache.fetch(torrent["id"])
    if not cache_record:
        _tmp = cache.get_torrent_id(torrent['hash'])
        if _tmp:
            cache.update_torrent_id(torrent["id"], old_torrent_id=_tmp)
            cache_record = cache.fetch(torrent["id"])
        else:
            logger.warning(f"Skipping default\{torrent['filename']} since its an unknown entity")
            return
    if cache_record.type == "movie":
        return movies(torrent)
    elif cache_record.type == "tv":
        return shows(torrent)
    
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
                logger.debug(f"Updated:\n\tStream path:{strm_path}\n\tDirect link:{direct_link}")
            else:
                pass
    except FileNotFoundError:
        # The file doesn't exist, so create it with the new contents
        with open(strm_path, 'w') as file:
            file.write(direct_link)
        logger.debug(f"Created:\n\tStream path:{strm_path}\n\tDirect link:{direct_link}")

def is_expired(json_date):
    try:
        # Parse the JSON-formatted date string into a datetime object
        date_obj = dt_parser.parse(json_date)
        
        # Get the current datetime
        current_datetime = datetime.datetime.utcnow()
        
        # Compare the parsed date with the current datetime
        return date_obj.timestamp() + SEVEN_DAYS < current_datetime.timestamp()
    except ValueError:
        # Handle invalid date format
        return False
    
def sort_downloads(downloads = [], _dict = {}):
    for download_info in downloads:
        _dict[download_info["link"]] = download_info
    for link in _dict:
        if is_expired(_dict[link]["generated"]):
            del _dict[link]
    return _dict

def resolve_media_type(folder_name):
    tv_regex = re.compile(r"[\W](S[0-9]{2}|SEASON|COMPLETE|[^457a-z\W\s]-[0-9]+)", re.RegexFlag.IGNORECASE)
    movie_regex = re.compile(r"(19|20)([0-9]{2} ?\.?)")
    if tv_regex.search(folder_name):
        return "tv"
    if movie_regex.search(folder_name):
        return "movie"
    
    return "unknown"
    
def sort_torrents(torrents, downloads, _dict = {}):
    for torrent in torrents:
        torrent["direct_links"] = {}
        hash = torrent["hash"].lower()
        if hash in _dict or torrent["status"] != "downloaded":
            continue
        for link in torrent["links"]:
            if link not in downloads:
                continue
            torrent["direct_links"][link] = downloads[link]
        torrent["type"] = resolve_media_type(torrent["filename"])
        _dict[hash] = torrent

    return _dict

    
def error_string(ex: Exception) -> str:
    return '\n'.join([
        ''.join(traceback.format_exception_only(None, ex)).strip(),
        ''.join(traceback.format_exception(None, ex, ex.__traceback__)).strip()
    ])
    
def try_folder_resolution(type, torrent):
    if not torrents:
        logger.error("Empty torrents list. Check internet connection or RD API key.")
        return
    try:
        if type == 'movie':
            movies(torrent)
        elif type == 'tv':
            shows(torrent)
        else:
            unknown(torrent)
    except Exception as ex:
        ex_string = error_string(ex)
        ex_string = ex_string.replace("\n", "\n\t")
        logger.error(f"{type}\{torrent['filename']} could not be resolved\n\tDetails: {ex_string}")

def manage_corrections(corrections: list[Correction]):
    global CORRECTIONS_FILE_LOCATION
    _corrections: list[Correction] = []
    try:
        if not os.path.isfile(CORRECTIONS_FILE_LOCATION):
            return _corrections
        with open(CORRECTIONS_FILE_LOCATION, "r+", encoding="utf-8") as corrections_file:
            for line in corrections_file.readlines():
                _values = line.split(",")
                correction = Correction(tmdb_id=_values[0].strip(),
                                        type=_values[1].strip(), hash=_values[2].strip().lower())
                omit_correction = False
                for former_correction in corrections:
                    if former_correction.hash == correction.hash and former_correction.done:
                        omit_correction = True
                        break
                if not omit_correction:
                    _corrections.append(correction)
            corrections_file.seek(0)
            corrections_file.truncate()
            for pending in _corrections:
                corrections_file.write(f"{pending.tmdb_id},{pending.type},{pending.hash}\n")
    except Exception as ex:
        ex_string = error_string(ex)
        ex_string = ex_string.replace("\n", "\n\t")
        logger.error(f"Unable to load corrections\n\tException Info: {ex_string}")
    finally:
        return _corrections

seconds_passed = 0
SECONDS_IN_A_DAY = 24 * 60 * 60

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Debrid Media Organizer v1.2")
    parser.add_argument('-rc', '--run-corrections', action='store_true', required=False,
                        help="Will exit after making all the corrections")
    parser.add_argument('-s', '--skip-media-reset', action='store_true', required=False,
                        help="If you're re-rerunning the script multiple times a day then choose this option.")
    parser.add_argument('-x', '--keep-running', action='store_true', required=False,
                        help="Runs the script as a service")
    parser.add_argument('-v', '--version', action='version',
                    version='Debrid Media Organizer 2.0.1', help="Show program's version number and exit.")
    args = parser.parse_args()

    downloads = sort_downloads(get_downloads())
    torrents = sort_torrents(get_torrents(), downloads)

    corrections: list[Correction] = []
    corrections = manage_corrections(corrections)
    for correction in corrections:
        torrents[correction.hash]["type"] = correction.type
        if not cache.fix_entry(correction):
            try:
                cache.save(torrents[correction.hash]["id"], correction.type, correction.tmdb_id, torrents[correction.hash]['filename'], correction.hash)
            except:
                continue
        try_folder_resolution(correction.type, torrents[correction.hash])
        correction.done = True
    corrections = manage_corrections(corrections)

    if args.run_corrections:
        exit()
    
    if not args.skip_media_reset:
        for hash in torrents:
            try_folder_resolution(torrents[hash]["type"], torrents[hash])
        
    if args.keep_running:
        sleep(5 * 60)
        seconds_passed = 5 * 60

    while args.keep_running:

        corrections: list[Correction] = []
        corrections = manage_corrections(corrections)
        for correction in corrections:
            torrents[correction.hash]["type"] = correction.type
            if not cache.fix_entry(correction):
                try:
                    cache.save(torrents[correction.hash]["id"], correction.type, correction.tmdb_id, torrents[correction.hash]['filename'], correction.hash)
                except:
                    continue
            try_folder_resolution(correction.type, torrents[correction.hash])
            correction.done = True
        corrections = manage_corrections(corrections)

        if seconds_passed > RESET_COUNTER:
            downloads = sort_downloads(get_downloads(), {})
            torrents = sort_torrents(get_torrents(), downloads, torrents)
            for hash in torrents:
                try_folder_resolution(torrents[hash]["type"], torrents[hash])

            seconds_passed = 0
        else:
            downloads = sort_downloads(get_downloads(200), downloads)
            old_torrents = cache.get_saved_torrent_ids()
            new_torrents = get_torrents((FOLDER_CHECK_FREQUENCY / 60) * 10)
            # : It's a new torrent if:
            #   - the torrent's ID is not a part of known torrent IDs
            #   - the torrent's filename is not a part of sorted torrents dict object
            #   - any of the files belonging to the torrent do not have a valid direct link
            new_torrents = [torrent for torrent in new_torrents if torrent["id"] not in old_torrents or torrent["hash"] not in torrents or torrents[torrent["hash"]]["id"] != torrent["id"]]
            new_torrents = new_torrents + [torrents[hash] for hash in torrents if any([link not in downloads for link in torrents[hash]["links"]])]
            new_torrents = sort_torrents(new_torrents, downloads, {})
            for hash in new_torrents:
                try_folder_resolution(new_torrents[hash]["type"], new_torrents[hash])
            torrents = {**torrents, **new_torrents}
        
        sleep(FOLDER_CHECK_FREQUENCY)
        seconds_passed = seconds_passed + FOLDER_CHECK_FREQUENCY

        
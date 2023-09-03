import re
import PTN

def sanitise_title_for_windows_folder_name(title):
    return re.sub(r'[:/\\*?"<>|\.$]', " ", title)

def naive_get_movie_title_and_year(folder_name: str):
    year_match = re.search(
        r"^(.+?)(?=\s?(?:\()?(\d{4})(?:\))?\s?)", folder_name, re.IGNORECASE
    )

    year = None
    title = None
    
    if year_match:
        # Extract the movie title and year from the file name
        title = (
            year_match.group(1)
            .split("- ")[-1]
            .split("= ")[-1]
            .split(" – ")[-1]
            .replace(".", " ")
            .strip()
            .replace("_", " ")
            .strip()
            .replace("-", " ")
            .strip()
        )

        year = year_match.group(2)

    else:
        # If the year is not present, set it to an empty string
        title = (
            folder_name.replace(".", " ")
            .replace("_", " ")
            .replace(" - ", " ")
            .replace(" = ", " ")
            .strip()
        )

    return [year, title]

video_extensions = [
    ".webm",
    ".mkv",
    ".flv",
    ".vob",
    ".ogv",
    ".ogg",
    ".rrc",
    ".gifv",
    ".mng",
    ".mov",
    ".avi",
    ".qt",
    ".wmv",
    ".yuv",
    ".rm",
    ".asf",
    ".amv",
    ".mp4",
    ".m4p",
    ".m4v",
    ".mpg",
    ".mp2",
    ".mpeg",
    ".mpe",
    ".mpv",
    ".m4v",
    ".svi",
    ".3gp",
    ".3g2",
    ".mxf",
    ".roq",
    ".nsv",
    ".flv",
    ".f4v",
    ".f4p",
    ".f4a",
    ".f4b",
    ".mod",
    ".ts",
    ".m2ts"
]

# PTN derived methods

def get_movie_info_from_torrent_name(folder_name: str):
    title = None
    year = None

    movie_guessed_info = PTN.parse(folder_name, True, True)

    if "title" not in movie_guessed_info:
        title = folder_name
    else:
        title = movie_guessed_info["title"]

    if "year" in movie_guessed_info:
        year = movie_guessed_info.get("year", [])[0]

    return [title, year]

def get_show_info_from_torrent_name(folder_name: str):
    title = None
    season = None
    episodes = []
    year = None

    series_guessed_info = PTN.parse(folder_name, standardise=True, coherent_types=True)

    if "title" not in series_guessed_info or series_guessed_info["title"] == "" :
        title = folder_name
    else:
        title = series_guessed_info["title"]

    if "season" not in series_guessed_info:
        pass
    else:
        season = series_guessed_info.get("season", [1])[0]

    if "episode" not in series_guessed_info:
        pass
    else:
        episodes = series_guessed_info.get("episode", [])

    if "year" in series_guessed_info:
        year = series_guessed_info.get("year", [])[0]

    return [title, year, season, episodes]

class Correction:
    folder_name = None
    tmdb_id = None
    type = None
    done = False
    def __init__(self, tmdb_id, type, folder_name) -> None:
        self.tmdb_id = int(tmdb_id)
        self.type = type
        self.folder_name = folder_name

__all__ = [
    "sanitise_title_for_windows_folder_name",
    "get_movie_info_from_torrent_name",
    "get_show_info_from_torrent_name",
    "Correction"
]
import sys
from urllib import request as URL_Request, error as URL_Error
import requests
from settings import _RD_API_KEY

base_uri = "https://api.real-debrid.com/rest/1.0"

headers = {
  'Authorization': f'Bearer {_RD_API_KEY}'
}

def get_torrents(limit: int = 2500):
    torrents = []
    page = 1
    total_received = 0
    limit = limit if limit < 2500 else 2500
    max_items = sys.maxsize if limit == 2500 else limit
    url = base_uri + f"/torrents?page={page}&limit={limit}"
    try:
        res = requests.get(url, headers=headers)
        while res.status_code == 200 and total_received < max_items:
            torrents = torrents + res.json()
            total_received = total_received + limit
            page = page + 1
            url = base_uri + f"/torrents?page={page}&limit={limit}"
            res = requests.get(url, headers=headers)
    except:
        pass
    return torrents

def get_downloads(limit: int = 2500):
    downloads = []
    page = 1
    total_received = 0
    limit = limit if limit < 2500 else 2500
    max_items = sys.maxsize if limit == 2500 else limit
    url = base_uri + f"/downloads?page={page}&limit={limit}"
    try:
        res = requests.get(url, headers=headers)
        while res.status_code == 200 and total_received < max_items:
            downloads = downloads + res.json()
            total_received = total_received + limit
            page = page + 1
            url = base_uri + f"/downloads?page={page}&limit={limit}"
            res = requests.get(url, headers=headers)
    except:
        pass
    return downloads

def get_torrent_info(torrent_id):
    try:
        url = base_uri + f"/torrents/info/{torrent_id}"
        res = requests.get(url, headers=headers)
        return res.json()
    except:
        return None

def get_resource(resource_uri):
    payload = {
        "link": resource_uri
    }
    url = base_uri + f"/unrestrict/link"
    res = requests.post(url, data=payload, headers=headers)
    return res.json()

def get_direct_link(resource_uri):
    payload = {
        "link": resource_uri
    }
    url = base_uri + f"/unrestrict/link"
    res = requests.post(url, data=payload, headers=headers)
    return res.json()["download"]

def check_link(url):
    try:
        # Send a request to the URL
        response = URL_Request.urlopen(url)
        # Check if the response status code indicates success (e.g., 200 OK)
        if response.getcode() == 200:
            return True
        else:
            return False
    except URL_Request.HTTPError as e:
        return False
    except URL_Error.URLError as e:
        return False
    except Exception as e:
        return True

def check_torrent_health(torrent_id):
    torrent_info = get_torrent_info(torrent_id)
    if torrent_info["status"] == "dead":
        return reinstate_torrent(torrent_info["hash"])
    for _link in torrent_info["links"]:
        try:
            link = get_direct_link(_link)
            if not check_link(link):
                return False
        except:
            return False
    return True

def read_initial_bytes(url, n = 512 * 1024):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        bytes_read = 0
        while bytes_read < n:
            chunk_size = min(1024, n - bytes_read)
            chunk = response.raw.read(chunk_size)
            if not chunk:
                break
            bytes_read += len(chunk)
        return True
    except:
        return False
        
def reinstate_torrent(hash):
    pass

__all__ = ["get_torrents", "get_downloads", "get_torrent_info", "get_resource", "get_direct_link", "read_initial_bytes"]
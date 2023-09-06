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
    url = base_uri + f"/torrents?page={page}&limit={limit}"
    try:
        res = requests.get(url, headers=headers)
        while(res.status_code == 200):
            torrents = torrents + res.json()
            page = page + 1
            url = base_uri + f"/torrents?page={page}&limit={limit}"
            res = requests.get(url, headers=headers)
    except:
        pass
    return torrents

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
        
def reinstate_torrent(hash):
    pass

__all__ = ["get_torrents", "get_torrent_info", "get_resource", "get_direct_link"]
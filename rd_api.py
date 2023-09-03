import requests
from settings import _RD_API_KEY

base_uri = "https://api.real-debrid.com/rest/1.0"

headers = {
  'Authorization': f'Bearer {_RD_API_KEY}'
}

def get_torrents():
    torrents = []
    page = 1
    url = base_uri + f"/torrents?page={page}&limit=2500"
    try:
        res = requests.get(url, headers=headers)
        while(res.status_code == 200):
            torrents = torrents + res.json()
            page = page + 1
            url = base_uri + f"/torrents?page={page}&limit=2500"
            res = requests.get(url, headers=headers)
    except:
        pass
    return torrents

def get_torrent_info(torrent_id):
    url = base_uri + f"/torrents/info/{torrent_id}"
    res = requests.get(url, headers=headers)
    return res.json()

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

__all__ = ["get_torrents", "get_torrent_info", "get_resource", "get_direct_link"]
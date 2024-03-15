import requests
import urllib.parse


def get_annotate(text: str, kwargs: dict = {}) -> dict:
    kwargs["text"] = text
    base_url = "https://api.dbpedia-spotlight.org/en/annotate?"
    url_query = urllib.parse.urlencode(kwargs)
    url = base_url + url_query
    header = {"accept": "application/json"}

    res = requests.get(url, headers=header)
    res.raise_for_status()

    return res.json()

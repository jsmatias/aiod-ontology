import requests
import urllib.parse
from ratelimit import limits, sleep_and_retry


@sleep_and_retry
@limits(calls=10, period=60)
@limits(calls=1, period=1)
def get_classification_from_text(text: str, kwargs: dict = {}) -> dict:
    kwargs["text"] = text
    base_url = "https://api.dbpedia-spotlight.org/en/annotate?"
    url_query = urllib.parse.urlencode(kwargs)
    url = base_url + url_query
    header = {"accept": "application/json"}

    res = requests.get(url, headers=header)
    res.raise_for_status()

    topics = list(set(res.json()))

    return topics

import requests

from pathlib import Path
from ratelimit import limits, sleep_and_retry

from downloader.name_encode_decode import encode
from config import PAPERS_PATH


ACM_BASE_URL = "https://dl.acm.org/doi/pdf/"


@sleep_and_retry
@limits(calls=10, period=60)
@limits(calls=1, period=1)
def from_doi(doi: str, sub_dir: str = "misc"):
    url = ACM_BASE_URL + doi
    file_name = encode(doi)
    sub_dir_path = PAPERS_PATH / sub_dir
    path = sub_dir_path / file_name

    if not Path.is_dir(sub_dir_path):
        Path.mkdir(sub_dir_path)

    res = requests.get(url, timeout=60)
    if res.ok:

        if b"<!DOCTYPE html>" in res.content:
            print(">> Html data found, make sure you have access to this paper.")
        else:
            with open(path, "wb") as pdf_file:
                pdf_file.write(res.content)
            print(">> Ok")
    else:
        print(">> Failed to download the PDF. Status code:", res.status_code)

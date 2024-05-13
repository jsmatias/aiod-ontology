import requests

from pathlib import Path
from ratelimit import limits, sleep_and_retry

from downloader.name_encode_decode import encode
from config import PAPERS_PATH
from utils.errors import ExistingFileError, NotPDFContentError


ACM_BASE_URL = "https://dl.acm.org/doi/pdf/"


@sleep_and_retry
@limits(calls=10, period=60)
@limits(calls=1, period=1)
def fetch_from_doi(doi: str, sub_dir: str = "misc", overwrite: bool = False):
    url = ACM_BASE_URL + doi
    file_name = encode(doi)
    sub_dir_path = PAPERS_PATH / sub_dir
    path = sub_dir_path / file_name

    if not Path.is_dir(sub_dir_path):
        Path.mkdir(sub_dir_path)

    if path.is_file() and not overwrite:
        raise ExistingFileError(
            "This file already exists! To overwrite it, use `overwrite=True`."
        )

    res = requests.get(url, timeout=60)
    if res.ok:

        if b"<!DOCTYPE html>" in res.content:
            raise NotPDFContentError(
                "Html content found, make sure you have access to this paper."
            )

        else:
            with open(path, "wb") as pdf_file:
                pdf_file.write(res.content)
            return
    res.raise_for_status()

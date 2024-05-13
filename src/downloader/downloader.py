from requests import HTTPError
import downloader.acm as acm
from config import DATA_PATH
from tqdm import tqdm


def _load_named_list(name: str) -> list:
    path = DATA_PATH / "data" / "lists" / (name + ".txt")
    with open(path, "r") as f:
        named_list = f.read().strip().split("\n")
    dois = [row.split()[0] for row in named_list]
    return dois


def download_from_doi(*dois: str, sub_dir: str, overwrite: bool = False):
    """
    Download papers from DOIs.

    Args:
        *dois (str): DOIs of papers to download.
        sub_dir (str): Subdirectory to save downloaded papers.
        overwrite (bool, optional): Flag to overwrite existing files. Defaults to False.
    """
    for doi in tqdm(dois):
        try:
            acm.fetch_from_doi(doi, sub_dir, overwrite)

        except HTTPError as err:
            print(f"{doi}: {err}")
        except Exception as err:
            print(f"{doi}: {err.args[0]}")
        else:
            print(f"{doi}: Fetched!")


def download(named_list: str, overwrite: bool = False):
    """
    Download papers from a named list.

    Args:
        named_list (str): Name of the list containing DOIs of papers to download.
        overwrite (bool, optional): Flag to overwrite existing files. Defaults to False.
    """
    dois = _load_named_list(named_list)
    download_from_doi(*dois, sub_dir=named_list, overwrite=overwrite)

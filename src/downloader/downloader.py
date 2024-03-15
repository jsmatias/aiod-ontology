import downloader.acm as acm
from config import DATA_PATH
from tqdm import tqdm


def _load_named_list(name: str) -> list:
    path = DATA_PATH / "data" / "lists" / (name + ".txt")
    with open(path, "r") as f:
        named_list = f.read().strip().split("\n")
    dois = [row.split()[0] for row in named_list]
    return dois


def download_from_doi(*dois: str, sub_dir: str):
    for doi in tqdm(dois):
        acm.from_doi(doi, sub_dir)


def download(named_list: str):
    dois = _load_named_list(named_list)
    download_from_doi(*dois, sub_dir=named_list)

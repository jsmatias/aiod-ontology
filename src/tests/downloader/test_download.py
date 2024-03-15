import fitz
import responses
import shutil

from pathlib import Path

import downloader

from config import PAPERS_PATH
from downloader import name_encode_decode

RESOURCES_PATH = Path(__file__).parent.parent / "resources"


def test_download_from_doi():

    doi_list = ["10.1145/2680821.2680824", "10.1145/3359061.3361084"]
    tmp_dir = PAPERS_PATH / "tmp"
    files = [tmp_dir / name_encode_decode.encode(doi) for doi in doi_list]

    with responses.RequestsMock() as mocked_requests:
        for doi in doi_list:
            doc = fitz.open(RESOURCES_PATH / name_encode_decode.encode(doi))
            first_page_content = doc[0].get_text()

            mocked_requests.add(
                method="GET",
                url=f"https://dl.acm.org/doi/pdf/{doi}",
                body=first_page_content
            )

        downloader.download_from_doi(*doi_list, sub_dir="tmp")

        assert Path.is_file(files[0])
        assert Path.is_file(files[1])

        shutil.rmtree(tmp_dir)
        assert not Path.is_dir(tmp_dir)

from pathlib import Path

from downloader import name_encode_decode
from reader.paper import Paper


RESOURCES_PATH = Path(__file__).parent.parent / "resources"


def test_paper_loader():
    file_name = "10_1145-2680821_2680824.pdf"
    title = "Performance and Fairness Issues in Big Data Transfers"
    keywords = ["big data transfer protocols", "fairness", "performance"]
    doi = name_encode_decode.decode(file_name)
    abstract = "we present performance and fairness analysis of two tcpbased (gridftp and fdt) " \
        + "and one udp-based (udt) big data transfer protocols. we perform long-haul performance " \
        + "experiments using a 10 gb/s national network, and conduct fairness tests in " \
        + "our 10 gb/s local network. our results show that gridftp with jumbo frames provides " \
        + "fast data transfers. gridftp is also fair in sharing bandwidth with competing background tcp"

    paper = Paper(files_path=RESOURCES_PATH, file_name=file_name, filename_has_doi=True)
    paper.load()

    assert title in paper._raw_text
    assert paper.keywords == keywords
    assert paper.doi == doi
    assert abstract in paper.abstract

import pytest
from pathlib import Path

from downloader import name_encode_decode
from reader.paper import Paper

RESOURCES_PATH = Path(__file__).parent.parent / "resources"


def test_paper_loader():
    file_name = "10_1145-2680821_2680824.pdf"
    title = "Performance and Fairness Issues in Big Data Transfers"
    keywords = ["big data transfer protocols", "fairness", "performance"]
    doi = name_encode_decode.decode(file_name)
    abstract = (
        "we present performance and fairness analysis of two tcpbased (gridftp and fdt) "
        "and one udp-based (udt) big data transfer protocols. we perform long-haul performance "
        "experiments using a 10 gb/s national network, and conduct fairness tests in "
        "our 10 gb/s local network. our results show that gridftp with jumbo frames provides "
        "fast data transfers. gridftp is also fair in sharing bandwidth with competing background tcp"
    )

    paper = Paper(files_path=RESOURCES_PATH, file_name=file_name, filename_has_doi=True)
    paper.load()

    assert title in paper._raw_text[0]
    assert paper.keywords == keywords
    assert paper.doi == doi
    assert abstract in paper.abstract


@pytest.fixture(params=range(8))
def scrambled_keywords(request):
    testing_text = {
        0: {
            "text": (
                "H.3.4 [Systems and Software]: Performance evaluation\n"
                "Keywords\n"
                "Big data transfer protocols; fairness; performance\n"
                "1.\n"
                "INTRODUCTION\n"
                "Large-s.."
            ),
            "expected_keywords": [
                "big data transfer protocols",
                "fairness",
                "performance",
            ]
        },
        1: {
            "text": (
                "H.3.4 [Systems and Software]: Performance evaluation\n"
                "keywords Big data transfer protocols; fairness; performance 1. INTRODUCTION Large-scale scientific"
            ),
            "expected_keywords": ["big data transfer protocols", "fairness", "performance"]
        },
        2: {
            "text": (
                "algorithms analysis;\n"
                "Additional Key Words and Phrases: Social Choice; Metric Distortion; Fairness; Copeland; Ranked Pairs\n"
                "1 INTRODUCTION"
            ),
            "expected_keywords": ["social choice", "metric distortion", "fairness", "copeland", "ranked pairs"]
        },
        3: {
            "text": (
                "Social choice\n"
                "KEYWORDS \n"
                "Data Science; Machine Learning; Problem Formulation; \n"
                "Fairness; Target Variable \n"
                "                                             Permission "
                "to make digital or hard copies of all or part of this work for personal \n"
                "or  classroom  use  is  granted\n"
            ),
            "expected_keywords": ["data science", "machine learning", "problem formulation", "fairness", "target variable"]
        },
        4: {
            "text": (
                "Keywords\n"
                "Fairness, FCFS, job scheduling, M/M/1, processor sharing,\n"
                "PS, queue disciplines, resource allocation, unfairness\n"
                "1. INTRODUCTION\n"
            ),
            "expected_keywords": [
                "fairness", "fcfs", "job scheduling", "m/m/1", 
                "processor sharing", "ps", "queue disciplines", "resource allocation", "unfairness"
            ]
        },
        5: {
            "text": (
                "Index Terms—software fairness, machine learning fairness\n"
                "I. INTRODUCTION\n"
            ),
            "expected_keywords": ["software fairness", "machine learning fairness"]
        },
        6: {
            "text": (
                "1. introduction\n"
                "key words\n"
                "big data transfer protocols;ai4europe;fairness;su8;a-cap;8su\n"
                "introduction\n"
            ),
            "expected_keywords": ["big data transfer protocols", "ai4europe", "fairness", "su8", "a-cap", "8su"]
        },
        7: {
            "text": (
                "KEYWORDS\n"
                "causal inference, variational inference, fairness in machine learning\n"
                "ACM Reference Format:\n"
            ),
            "expected_keywords": ["causal inference", "variational inference", "fairness in machine learning"]
        }
    }
    return testing_text[request.param]


def test_keywords_extraction(scrambled_keywords):
    paper = Paper(
        files_path=RESOURCES_PATH, file_name="fake_name.pdf", filename_has_doi=False
    )
    paper._raw_text = [scrambled_keywords["text"]]
    paper._extract_keywords_from_pdf_content()

    assert paper.keywords == scrambled_keywords["expected_keywords"]
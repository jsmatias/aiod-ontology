"""
Reads a single paper or a bulk of paper
"""
import json
import pandas as pd
from glob import glob
from pathlib import Path
from tqdm import tqdm
from .paper import Paper
from config import PAPERS_PATH, DATA_PATH


class Reader:
    def __init__(self) -> None:
        self.files_path = PAPERS_PATH
        self.cache_path = DATA_PATH / "reader" / "cache" / "papers.json"
        self.paper_list: list[Paper] = []
        self.cache: dict[str, dict] = {}
        self.dois_not_cached: list[str] = []

    def _load_paper_and_import_from_cache(self, dir: str,  paper_name: str, filename_has_doi: bool, pattern_to_replace: dict):
        paper = Paper(self.files_path / dir, paper_name, filename_has_doi, pattern_to_replace)
        paper.load()

        cached_paper = self.cache.get(paper.doi, None)
        if cached_paper is None:
            self.dois_not_cached.append(paper.doi)
        else:
            paper.import_from_dict(cached_paper)

        self.paper_list.append(paper)

    def reset(self):
        self.paper_list = []

    def load(self, named_list: str, filename_has_doi: bool = True, pattern_to_replace: dict = {}):
        self.load_cache()

        papers_paths = glob(str(self.files_path / named_list / "*.pdf"))
        pbar = tqdm(papers_paths)
        for paper_path in pbar:
            paper_name = paper_path.split("/")[-1]
            pbar.set_description(f"Processing {paper_name}")
            self._load_paper_and_import_from_cache(named_list, paper_name, filename_has_doi, pattern_to_replace)
        self.clean_cache()

    def load_single_paper(self, dir: str, file_name: str, filename_has_doi: bool = True, pattern_to_replace: dict = {}) -> int:

        self.load_cache()
        self._load_paper_and_import_from_cache(dir, file_name, filename_has_doi, pattern_to_replace)
        self.clean_cache()
        return len(self.paper_list) - 1

    def load_cache(self):
        if Path.is_file(self.cache_path):
            with open(self.cache_path, "r") as f:
                self.cache = json.load(f)

    def clean_cache(self):
        self.cache = {}

    def dump(self):
        cache = {paper.doi: paper.export_to_dict() for paper in self.paper_list}

        with open(self.cache_path, "w") as f:
            json.dump(cache, f)

    def extract_metadata(self):
        if not self.paper_list:
            raise Exception("There's no paper loaded.")
        pbar = tqdm(self.paper_list)
        for paper in pbar:
            pbar.set_description(f"Processing {paper.doi}")
            paper.get_metadata()

    def extract_classification(self, *from_source: str):
        pbar = tqdm(self.paper_list)
        for paper in pbar:
            pbar.set_description(f"Processing {paper.doi}")
            for source in from_source:
                match source.lower():
                    case "acm":
                        try:
                            paper.extract_acm_topics()
                        except Exception:
                            pass
                    case "dbpedia":
                        try:
                            paper.extract_dbpedia_topics()
                        except Exception:
                            pass
                    case _:
                        raise Exception("Not implemented.")

    def get_metadata(self, format: str = "dict") -> list[dict] | pd.DataFrame:
        """
        Args:
            format: accepts 'dict' or 'dataframe'
        returns: A list of dictionaries containing the metadata extracted from the
            paper of a pandas dataframe.
        """

        papers_details = []
        for paper in self.paper_list:
            papers_details.append(
                {
                    "file_name": paper.file_name,
                    "doi": paper.doi,
                    "title": paper.title,
                    "authors": ";".join(paper.author),
                    "journal": paper.journal,
                    "publisher": paper.publisher,
                    "year": paper.year,
                    "keywords": ";".join(paper.keywords),
                    "topics": ";".join(paper.topics),
                }
            )

        if format == "dict":
            return papers_details
        elif format == "dataframe":
            papers_df = pd.DataFrame(papers_details)
            return papers_df
        else:
            raise TypeError("format must be 'dict' or 'dataframe'")

    def get_data(self, raw=False) -> dict:
        """"""
        papers_content = []
        for paper in self.paper_list:
            papers_content.append(
                {
                    "doi": paper.doi,
                    "text": paper._raw_text if raw else paper.text,
                }
            )
        return papers_content

    def source(self) -> str:
        return self.files_path

    def numb_papers(self):
        return len(self.paper_list)

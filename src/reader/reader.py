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
    def __init__(self, named_list: str) -> None:
        self.named_list = named_list
        self.cache_file = named_list + ".json"
        self.files_path = PAPERS_PATH
        self.cache_path = DATA_PATH / "reader" / "cache"
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

    def load(self, filename_has_doi: bool = True, pattern_to_replace: dict = {}, from_inc: int | None = None, to_exc: int | None = None):

        self.load_cache()

        papers_paths = glob(str(self.files_path / self.named_list / "*.pdf"))[from_inc: to_exc]
        pbar = tqdm(papers_paths)
        for paper_path in pbar:
            paper_name = paper_path.split("/")[-1]
            pbar.set_description(f"Processing {paper_name}")
            self._load_paper_and_import_from_cache(self.named_list, paper_name, filename_has_doi, pattern_to_replace)

    def load_single_paper(self, dir: str, file_name: str, filename_has_doi: bool = True, pattern_to_replace: dict = {}) -> int:

        self.load_cache()
        self._load_paper_and_import_from_cache(dir, file_name, filename_has_doi, pattern_to_replace)
        return len(self.paper_list) - 1

    def load_cache(self):
        cache_file_path = self.cache_path / self.cache_file
        if Path.is_file(cache_file_path):
            with open(cache_file_path, "r") as f:
                self.cache = json.load(f)

    def clean_cache(self):
        self.cache = {}

    def dump(self, overwrite: bool = False):
        if overwrite:
            self.clean_cache()
        for paper in self.paper_list:
            self.cache[paper.doi] = paper.export_to_dict()
        with open(self.cache_path / self.cache_file, "w") as f:
            json.dump(self.cache, f)

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

    def export_as_klink_input(self, classification_source):
        topics_src = f"topics_{classification_source}"
        cols_dict = {
            "keywords": "DE",
            "title": "TI",
            "authors": "AU",
            "publisher": "SO",
            topics_src: "SC",
            "year": "PY",
        }
        data_to_export = self.get_metadata("dataframe").fillna("")
        mask = (data_to_export["keywords"] != "") & (data_to_export[topics_src] != "")
        data_to_export = data_to_export[mask]
        data_to_export.rename(columns=cols_dict, inplace=True)

        data_to_export = data_to_export[list(cols_dict.values())]
        data_to_export.to_csv(DATA_PATH / "klink2" / f"{self.named_list}.tsv", sep="\t", index=False)
        return data_to_export

    def get_metadata(self, format: str = "dict") -> list[dict] | pd.DataFrame:
        """
        Args:
            format: accepts 'dict' or 'dataframe'
        returns: A list of dictionaries containing the metadata extracted from the
            paper of a pandas dataframe.
        """

        papers_details = []
        for paper in self.paper_list:
            paper_data = {
                "file_name": paper.file_name,
                "doi": paper.doi,
                "title": paper.title,
                "authors": ";".join(paper.author),
                "journal": paper.journal,
                "publisher": paper.publisher,
                "year": paper.year,
                "keywords": ";".join(paper.keywords),
            }
            for key in paper.topics:
                paper_data[f"topics_{key}"] = ";".join(paper.topics[key])
            papers_details.append(paper_data)

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

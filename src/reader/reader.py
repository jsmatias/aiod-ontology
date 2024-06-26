"""
Reads a single paper or a bulk of paper
"""

import json
from typing import Literal
import pandas as pd
from glob import glob
from pathlib import Path
from tqdm import tqdm
from .paper import Paper
from config import PAPERS_PATH, DATA_PATH


class Reader:
    def __init__(self, named_list: str) -> None:
        """
        Initialize the Reader object.

        Args:
            named_list (str): The name of the list.
        """
        self.named_list = named_list
        self.cache_file = named_list + ".json"
        self.files_path = PAPERS_PATH
        self.cache_path = DATA_PATH / "reader" / "cache"
        self.paper_list: list[Paper] = []
        self.cache: dict[str, dict] = {}
        self.dois_not_cached: list[str] = []

    def _load_paper_and_import_from_cache(
        self,
        dir: str,
        paper_name: str,
        filename_has_doi: bool,
        pattern_to_replace: dict,
    ):
        """
        Load paper content from the PDF file
        and import metadata including processed text from cache.

        Args:
            dir (str): Directory.
            filename_has_doi (bool): Whether the file is named with DOI pattern.
                When set to `True` the DOI will be extract from the name using the
                `pattern_to_replace`.
            pattern_to_replace (dict): Pattern to replace.
                e.g.: filename = file_10_1145-3351095_00000000.txt
                      pattern_to_replace = {'_': '.', '-':'/'}
        """
        paper = Paper(
            self.files_path / dir, paper_name, filename_has_doi, pattern_to_replace
        )
        paper.load()

        cached_paper = self.cache.get(paper.doi, None)
        if cached_paper is None:
            self.dois_not_cached.append(paper.doi)
        else:
            paper.import_from_dict(cached_paper)

        self.paper_list.append(paper)

    def reset(self):
        """Reset paper list."""
        self.paper_list = []

    def load(
        self,
        filename_has_doi: bool = True,
        pattern_to_replace: dict = {},
        from_inc: int | None = None,
        to_exc: int | None = None,
    ):
        """
        Load papers from the specified directory.

        Args:
            filename_has_doi (bool, optional): Whether the file is named with DOI pattern. Defaults to True.
                When set to `True` the DOI will be extract from the name using the
                `pattern_to_replace`.
            pattern_to_replace (dict): Pattern to replace. Defaults to {}.
                e.g.: filename = file_10_1145-3351095_00000000.txt
                      pattern_to_replace = {'_': '.', '-':'/'}
            from_inc (int | None, optional): Index to start loading papers (inclusive). Defaults to None.
            to_exc (int | None, optional): Index to stop loading papers (exclusive). Defaults to None.
        """
        self.load_cache()

        papers_paths = glob(str(self.files_path / self.named_list / "*.pdf"))[
            from_inc:to_exc
        ]
        pbar = tqdm(papers_paths)
        for paper_path in pbar:
            paper_name = paper_path.split("/")[-1]
            pbar.set_description(f"Processing {paper_name}")
            self._load_paper_and_import_from_cache(
                self.named_list, paper_name, filename_has_doi, pattern_to_replace
            )

    def load_single_paper(
        self,
        dir: str,
        file_name: str,
        filename_has_doi: bool = True,
        pattern_to_replace: dict = {},
    ) -> int:
        """
        Load a single paper.

        Args:
            dir (str): Directory.
            file_name (str): Name of the file.
            filename_has_doi (bool): Whether the file is named with DOI pattern.
                When set to `True` the DOI will be extract from the name using the
                `pattern_to_replace`.
            pattern_to_replace (dict): Pattern to replace.
                e.g.: filename = file_10_1145-3351095_00000000.txt
                      pattern_to_replace = {'_': '.', '-':'/'}

        Returns:
            int: Length of paper list.
        """

        self.load_cache()
        self._load_paper_and_import_from_cache(
            dir, file_name, filename_has_doi, pattern_to_replace
        )
        return len(self.paper_list) - 1

    def load_cache(self):
        """Load processed information from cache if it exists."""
        cache_file_path = self.cache_path / self.cache_file
        if Path.is_file(cache_file_path):
            with open(cache_file_path, "r") as f:
                self.cache = json.load(f)

    def clean_cache(self):
        """Clean cache."""
        self.cache = {}

    def dump(self, overwrite: bool = False):
        """
        Dump cache to a json file.

        Args:
            overwrite (bool, optional): Deletes everything that was previously in the cache.
                Otherwise it will update it. Default is false.
        """
        if overwrite:
            self.clean_cache()
        for paper in self.paper_list:
            self.cache[paper.doi] = paper.export_to_dict()
        with open(self.cache_path / self.cache_file, "w") as f:
            json.dump(self.cache, f)

    def extract_metadata(self):
        """Extract metadata from an external source via API."""
        if not self.paper_list:
            raise Exception("There's no paper loaded.")
        pbar = tqdm(self.paper_list)
        for paper in pbar:
            pbar.set_description(f"Processing {paper.doi}")
            paper.get_metadata()

    def extract_classification(self, *from_source: str):
        """
        Extract classification topics using an external source.

        Args:
            from_source Literal["acm", "dbpedia"]: The name of the external source.
                TODO: Include CSO classifier
        """
        pbar = tqdm(self.paper_list)
        for paper in pbar:
            pbar.set_description(f"Processing {paper.doi}")
            for source in from_source:
                match source.lower():
                    case "acm":
                        try:
                            paper.extract_acm_topics()
                        except Exception as err:
                            print(f"{paper.doi}: {err}")
                    case "dbpedia":
                        try:
                            paper.extract_dbpedia_topics()
                        except Exception as err:
                            print(f"{paper.doi}: {err}")

                    case _:
                        raise Exception(
                            f"Classification from '{source}' is not implemented."
                        )

    def export_as_klink_input(self, classification_source) -> pd.DataFrame:
        """
        Export as Klink input to a tsv file.
        This is the file used by klink2 algorithm to build the ontology.

        Args:
            classification_source: Used to select which source will be used to
                export the topics from.

        Return (pd.DataFrame): The processed data as a klink input.
            Same as the exported to tsv file.

        Raises: Exception if the topics from `classification_source` is not
            present in the data.
        """
        topics_src = f"topics_{classification_source}"
        data_to_export = self.metadata_collection(data_format="dataframe").fillna("")

        if topics_src not in data_to_export.columns:
            msg = (
                f"Topics from {classification_source} no found in the data. "
                f"Use the method `extract_classification({classification_source})` and try again."
            )
            raise Exception(msg)
        cols_dict = {
            "keywords": "DE",
            "title": "TI",
            "authors": "AU",
            "publisher": "SO",
            topics_src: "SC",
            "year": "PY",
        }
        mask = (data_to_export["keywords"] != "") & (data_to_export[topics_src] != "")
        data_to_export = data_to_export[mask]
        data_to_export.rename(columns=cols_dict, inplace=True)

        data_to_export = data_to_export[list(cols_dict.values())]

        dir_path = DATA_PATH / "klink2" / self.named_list
        if not dir_path.is_dir():
            Path.mkdir(dir_path)

        data_to_export.to_csv(
            dir_path / f"{self.named_list}.tsv", sep="\t", index=False
        )
        return data_to_export

    def metadata_collection(
        self, data_format: Literal["dict", "dataframe"] = "dict"
    ) -> list[dict] | pd.DataFrame:
        """
        Args:
            data_format (Literal["dict", "dataframe"]): accepts 'dict' or 'dataframe'

        Returns (list[dict] | pd.DataFrame): If `data_format = 'dict'` A list of dictionaries containing the metadata extracted from the
            paper. If `data_format = 'dataframe'` it returns a pandas dataframe.
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

        if (data_format == "dict") and isinstance(papers_details, list):
            return papers_details
        elif data_format == "dataframe":
            papers_df = pd.DataFrame(papers_details)
            return papers_df
        else:
            raise ValueError("data_format must be 'dict' or 'dataframe'")

    def content_collection(self, raw: bool = False) -> list[dict]:
        """Get the text content of the papers.

        Args:
            raw (bool, option): If true the text content returned is the exact text with any processing. Default is False.

        Return (list[dict]): The list of dictionaries with text content from the papers.
        """
        papers_content = []
        for paper in self.paper_list:
            papers_content.append(
                {
                    "doi": paper.doi,
                    "text": paper._raw_text if raw else paper.text,
                }
            )
        return papers_content

    def source(self) -> Path:
        """Get path of the files."""
        return self.files_path

    def numb_papers(self) -> int:
        """Get the number of papers in the paper list"""
        return len(self.paper_list)

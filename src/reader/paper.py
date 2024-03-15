import re
import fitz
import numpy as np
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from utils.utils import extract_doi_from_str

from classifiers import dbpedia
from classifiers import acm
from downloader import name_encode_decode
from .metadata import Metadata


class Paper:
    """A simple abstraction layer for working on the paper object"""

    def __init__(
        self,
        files_path: str,
        file_name: str,
        filename_has_doi: bool = True,
        pattern_to_replace: dict = {},
        silent=True,
    ) -> None:
        """
        Args:
            files_path: "/path/to/files/"
            file_name: "my-paper.pdf"
            pattern_to_replace: only used when `from_filename` is set to True.
                This method will try to replace the keys of the dictionary by their corresponding values
                on the filename.
            from_filename: When set to `True` the method will try to find the doi pattern in the filename.
        """
        self.filename_has_doi = filename_has_doi
        self.pattern_to_replace = pattern_to_replace

        self.silent = silent
        self.file_name = file_name
        self.doi = self._get_doi_from_file_name() if filename_has_doi else ""
        self.full_path = files_path / self.file_name

        self._pdf_info = [{}]
        self._raw_text = ""
        self.text = ""

        self.title = ""
        self.author = []
        self.abstract = ""
        self.issn = ""
        self.url = ""
        self.number = ""
        self.journal = ""
        self.publisher = ""
        self.year = ""
        self.month = ""
        self.pages = ""
        self.keywords = []
        self.topics = {}

    def _get_doi_from_file_name(self) -> str:
        """Get doi from file name replacing a pattern if needed"""

        if self.pattern_to_replace:
            mod_name = ".".join(self.file_name.split(".")[:-1])
            for k, v in self.pattern_to_replace.items():
                mod_name = mod_name.replace(k, v)
        else:
            mod_name = name_encode_decode.decode(self.file_name)
        doi_list = extract_doi_from_str(mod_name)

        if len(doi_list) > 1:
            raise Exception("Multiple DOIs found.")
        if len(doi_list) == 0:
            raise Exception("No DOI found.")
        return doi_list[0]

    def _extract_abstract(self):
        """Tries to extract the abstract from the pdf content."""
        pattern_start = r"(?:\babstract\b)"
        pattern_end = r"(?=(?:\bccs concepts\b|\bkeywords\b|\bacm reference format\b|\bintroduction\b))"
        full_pattern = pattern_start + r"([\S\s]*?)" + pattern_end

        text = self._raw_text.replace("-\n", "")
        text = re.sub(r"\n+", " ", text)
        text = re.sub(r" {2,3}", " ", text)
        text = text.lower().strip()
        abstract_groups = re.findall(full_pattern, text)

        if len(abstract_groups) > 1:
            msg = f"Pattern error: Multiple abstracts found.\n{abstract_groups}"
            raise Exception(msg)

        self.abstract = abstract_groups[0].strip()

    def _extract_keywords_from_pdf_content(self):
        r"""Tries to extract keywords from the text.
        It assumes that the pattern is a list of words after the flag 'keywords' or 'key words'
        separated by any non-word character, excluding "\s" and "-".
        Full pattern:
          "(?:Keywords|Key words)[:\s]((?:(?:\w+(?:[-\s]\w+){,3})){1,6}(?:\w+(?:[-\s]\w+){0,3})(?:[^\s,\w]|\n\w+[^ \w]))"
        Ex.: keywords: test-word1, test-word2 word1, word2, last composed.
        """
        text = self._raw_text.replace("-\n", "")
        text = re.sub(r" {2,3}", " ", text)
        text = re.sub(r"\n{2,}", "\n", text)
        text = re.sub(r"(?<=[^ \w])\s|\s(?=[^ \w])", "", text)
        text = text.lower().strip()
        
        min_characters = 2
        min_words = 1
        max_words = 4

        min_keywords = 1
        max_keywords = 7

        start_pattern = r"(?:keywords|key words)[:\s]"
        # keyword_pattern = rf"\w+(?:[-\s]\w+){{{min_words-1},{max_words-1}}}"
        keyword_pattern = rf"(?:[\s]?[\w-]{{{min_characters},}}){{{min_words},{max_words}}}"
        separator_pattern = r"[^\s\w-]"  # e.g. ",", ";", "|", etc.
        separator = re.findall(
            rf"{start_pattern}{keyword_pattern}({separator_pattern})", text
        )
        if separator:
            # separator must have just one element
            separator = separator[0]
        else:
            keywords_list = []
            return keywords_list

        keyword_sep_pattern = f"{keyword_pattern}{separator}"
        end_pattern = rf"(?=[^\s\w{separator}]|\n\w+[^ \w])"  # full stop or a word wrapped around \n

        keywords_group_pattern = f"(?:{keyword_sep_pattern}){{{min_keywords},{max_keywords-1}}}(?:{keyword_pattern})"
        keywords_match_pattern = (
            rf"{start_pattern}({keywords_group_pattern}{end_pattern})"
        )
        print(keywords_match_pattern)

        keywords_group = re.findall(keywords_match_pattern, text)
        if not keywords_group:
            return self.keywords or []
        keywords_string = keywords_group[0]

        keywords_list = [
            keyword.strip().replace("\n", " ")
            for keyword in keywords_string.split(separator)
        ]

        if keywords_list and (keywords_list[-1] in ["acm reference format"]):
            del keywords_list[-1]

        if self.keywords and (self.keywords != keywords_list):
            print(
                "Keywords found from the metadata of the pdf differs from the ones found in the text."
            )

        self.keywords = [keyword.strip().lower() for keyword in keywords_list]

    def _extract_keywords_from_pdf_metadata(self):
        """Search for keywords in the pdf metadata"""
        if not self._pdf_info:
            raise Exception("No pdf info found.")

        keywords_list = []
        keywords_str = self._pdf_info[0].get("Keywords", "")
        if isinstance(keywords_str, bytes):
            keywords_str = str(keywords_str, encoding="utf-8")
        keywords_list = re.split(r"[^\s\w-]", keywords_str)
        self.keywords = [keyword.strip().lower() for keyword in keywords_list]

    def extract_keywords(self):
        if self.keywords and self.keywords[0]:
            return
        self._extract_keywords_from_pdf_metadata()
        if self.keywords and self.keywords[0]:
            return
        self._extract_keywords_from_pdf_content()

    def load(self):
        """Loads the PDF content and extracts keywords and abstract from file."""
        self.extract_pdf_info()
        self.extract_pdf_text()
        self._extract_abstract()
        self.extract_keywords()
        self.clean_text()

    def extract_acm_topics(self):
        """Gets the topics from ACM classification."""
        if not self.doi:
            raise Exception("DOI not set!")

        publisher = self.publisher.lower().strip()
        if publisher != "acm":
            raise Exception("This paper's publisher is not ACM!")

        topics = acm.get_classification_from_doi(self.doi)[1:]
        if topics and (topics[0].strip().lower() != self.title.lower().strip()):
            msg = f"The title in the topics extracted from '{publisher}' didn't match with '{self.title}'"
            raise Exception(msg)

        self.topics["acm"] = topics

    def extract_dbpedia_topics(self):
        if not self.abstract:
            self.topics["dbpedia"] = []
        try:
            res_dict = dbpedia.get_classification_from_text(self.abstract)
            self.topics["dbpedia"] = (
                [resource["@surfaceForm"] for resource in res_dict["Resources"]]
                if res_dict["Resources"]
                else []
            )
        except Exception as exc:
            raise exc

    def get_metadata(self):
        """Gets the metadata from external source via API."""
        if self.doi:
            metadata = Metadata().get_metadata_from_doi(self.doi)

            if not self.silent:
                print("Correct DOI? ", self.cross_validate_doi(metadata))

            self.title = metadata["title"] or self.title
            self.author = metadata["author"] or self.author
            self.issn = metadata["issn"] or self.issn
            self.url = metadata["url"] or self.url
            self.doi = metadata["doi"] or self.doi
            self.number = metadata["number"] or self.number
            self.journal = metadata["journal"] or self.journal
            self.publisher = metadata["publisher"] or self.publisher
            self.year = metadata["year"] or self.year
            self.month = metadata["month"] or self.month
            self.pages = metadata["pages"] or self.pages
            self.keywords = metadata["keywords"] or self.keywords
        else:
            raise Exception(f"DOI for this paper ({self.file_name}) not set.")

    def export_to_dict(self):
        pass

    def export_to_klink_input(self):
        pass

    def cross_validate_doi(self, metadata: dict) -> bool:
        """Check if title from metadata is in the text"""
        text = re.sub(r"\n", " ", self.text)
        text = re.sub(r"\s\s", " ", text)

        assertion = (self.doi == metadata["doi"]) and (
            re.sub(r"(?!\s)\W", "", metadata["title"]).lower().strip() in text
        )
        return assertion

    def clean_text(self):
        """Remove punctuation and special characters from the text"""

        # join words that are separated at the end of the line: e.g. dis-\parate
        text = self._raw_text.replace("-\n", "\n")
        # remove line breaks
        text = text.replace(r"\n", " ")
        text = re.sub(r"\s\s", " ", text)
        # remove any non-word character, excluding empty spaces.
        text = re.sub(r"(?!\s)\W", "", text).lower().strip()
        self.text = text

    def extract_pdf_info(self) -> list:
        """
        Extracts the metadata information of the PDF file if available.
        """

        fp = open(self.full_path, "rb")
        parser = PDFParser(fp)
        doc = PDFDocument(parser)
        info = doc.info
        self._pdf_info = info

    def extract_pdf_text(self) -> str:
        """
        Extract the text from the pdf file.
        """
        doc = fitz.open(self.full_path)
        text = ""
        for page in doc:
            text += page.get_text()
        self._raw_text = text

    def extract_doi(self) -> str:
        """Extracts DOI"""
        doi_list = []
        if self.filename_has_doi:
            filename = ".".join(
                self.file_name.split(".")[:-1]
            )  # remove filename extension
            for k, v in self.pattern_to_replace.items():
                filename = filename.replace(k, v)
            doi_list = extract_doi_from_str(filename)

        if not doi_list:
            doi_list = extract_doi_from_str(str(self._pdf_info))
        if not doi_list:
            doi_list = extract_doi_from_str(self._raw_text)

        self.doi = doi_list[0] if doi_list else ""

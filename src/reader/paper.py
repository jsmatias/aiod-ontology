from pathlib import Path
import re
import fitz
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from utils.utils import extract_doi_from_str

from .metadata import Metadata
from classifiers import dbpedia
from classifiers import acm
from downloader import name_encode_decode
from utils.errors import MissingDOIError, WrongPaperError


class Paper:
    """A simple abstraction layer for working on the paper object"""

    def __init__(
        self,
        files_path: str | Path,
        file_name: str,
        filename_has_doi: bool = True,
        pattern_to_replace: dict = {},
        silent=True,
    ) -> None:
        """
        Args:
            files_path: "/path/to/files/"
            file_name: "my-paper.pdf"
            filename_has_doi (bool, optional): Whether the file is named with DOI pattern. Defaults to True.
                When set to `True` the DOI will be extract from the name using the
                `pattern_to_replace`.
            pattern_to_replace (dict): Pattern to replace, only used when `from_filename` is set to True.
                Defaults to {}.
                e.g.: filename = file_10_1145-3351095_00000000.txt
                      pattern_to_replace = {'_': '.', '-':'/'}
        """
        assert file_name.split(".")[-1].lower() == "pdf", "Only PDF files are accepted."

        self.filename_has_doi = filename_has_doi
        self.pattern_to_replace = pattern_to_replace

        self.silent = silent
        self.file_name = file_name
        self.doi = self._get_doi_from_file_name() if filename_has_doi else ""
        self.full_path = Path(files_path) / self.file_name

        self._pdf_info = [{}]
        self._raw_text = []
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
        return doi_list[0].lower()

    def _extract_abstract(self):
        """Tries to extract the abstract from the pdf content."""
        pattern_start = r"(?:Abstract[^]])[-— ]?"
        pattern_end = r"(?:Index Terms|Categories and Subject|Keywords|Key words|CCS Concepts|ACM Reference Format)"
        full_pattern = "(?si)" + pattern_start + "(.*?)" + pattern_end

        text = "\n".join(self._raw_text[:2]).replace("-\n", "")
        text = re.sub(r"\n+", " ", text)
        text = re.sub(r" {2,3}", " ", text)
        text = text.lower().strip()
        abstract_groups = re.findall(full_pattern, text)

        if len(abstract_groups) > 1:
            msg = f"Pattern error: Multiple abstracts found.\n{abstract_groups}"
            raise Exception(msg)

        self.abstract = abstract_groups[0].strip()

    def _extract_keywords_from_pdf_content(self):
        text = "\n".join(self._raw_text[:2])
        start_pattern = (
            r"(?:Key words and Phrases|KEYWORDS|Key words|Index Terms)[-—\s:]"
        )
        keyword_pattern = r"(.*?)"
        end_pattern = r"(?:[1I]\.?[ \n]Introduction|Introduction|ACM|(?:\w+[ -]){4})"
        keywords_match_pattern = rf"(?si){start_pattern}{keyword_pattern}{end_pattern}"

        keywords_group = re.findall(keywords_match_pattern, text)
        if not keywords_group:
            self.keywords = []
            return
        keywords_string = keywords_group[0]

        separator_pattern = r"[^\s\w-]"  # e.g. ",", ";", "|", etc.
        separator = re.findall(separator_pattern, keywords_string)

        if separator:
            separator = separator[0]
        else:
            self.keywords = []
            return

        keywords_list = [
            keyword.strip().replace("-\n", "").replace("\n", "").lower()
            for keyword in keywords_string.split(separator)
        ]

        if self.keywords and (self.keywords != keywords_list):
            print(
                f"Keywords found from the metadata ({self.keywords}) of the pdf differs from the ones found in the text: {keywords_list}"
            )

        self.keywords = keywords_list

    def _extract_keywords_from_pdf_metadata(self):
        """Search for keywords in the pdf metadata"""
        if not self._pdf_info:
            raise Exception("No pdf info found.")

        keywords_list = []
        keywords_str = self._pdf_info[0].get("Keywords", "")
        if isinstance(keywords_str, bytes):
            keywords_str = str(keywords_str, encoding="utf-8")
        keywords_list = re.split(r"[^\s\w-]", keywords_str)
        while "" in keywords_list:
            keywords_list.pop(keywords_list.index(""))
        self.keywords = [keyword.strip().lower() for keyword in keywords_list]

    def extract_keywords(self):
        if self.keywords and self.keywords[0]:
            return
        try:
            self._extract_keywords_from_pdf_metadata()
        except Exception:
            self.keywords = []
        if self.keywords and self.keywords[0]:
            return
        try:
            self._extract_keywords_from_pdf_content()
        except Exception:
            self.keywords = []

    def load(self):
        """Loads the PDF content and extracts keywords and abstract from file."""
        self.extract_pdf_info()
        self.extract_pdf_text()
        try:
            self._extract_abstract()
        except Exception:
            pass
        self.extract_keywords()
        self.clean_text()

    def extract_acm_topics(self):
        """Gets the topics from ACM classification."""
        if not self.doi:
            raise MissingDOIError("DOI not set!")

        topics = acm.get_classification_from_doi(self.doi)
        if topics and (topics[0].strip().lower() != self.title.lower().strip()):
            msg = (
                f"The title '{topics[0]}' in the topics extracted from ACM didn't match with '{self.title}'."
                "Ignoring this classification."
            )
            raise WrongPaperError(msg)

        self.topics["acm"] = topics[1:]

    def extract_dbpedia_topics(self):
        if not self.abstract:
            self.topics["dbpedia"] = []
        try:
            res_dict = dbpedia.get_classification_from_text(self.abstract)
            topics = (
                [resource["@surfaceForm"] for resource in res_dict["Resources"]]
                if res_dict["Resources"]
                else []
            )
            self.topics["dbpedia"] = list(set(topics))

        except Exception as exc:
            raise exc

    def get_metadata(self) -> None:
        """Gets the metadata from external source via API."""
        if self.doi:
            metadata: dict = Metadata().get_metadata_from_doi(self.doi)

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

    def import_from_dict(self, paper: dict):
        for k, v in paper.items():
            setattr(self, k, v)

    def export_to_dict(self) -> dict:
        metadata = {
            key: (
                str(self.__dict__[key])
                if isinstance(self.__dict__[key], Path)
                else self.__dict__[key]
            )
            for key in [
                "filename_has_doi",
                "pattern_to_replace",
                "silent",
                "file_name",
                "doi",
                "full_path",
                "title",
                "author",
                "abstract",
                "issn",
                "url",
                "number",
                "journal",
                "publisher",
                "year",
                "month",
                "pages",
                "keywords",
                "topics",
            ]
        }
        return metadata

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
        text = "\n".join(self._raw_text).replace("-\n", "\n")
        # remove line breaks
        text = text.replace(r"\n", " ")
        text = re.sub(r"\s\s", " ", text)
        # remove any non-word character, excluding empty spaces.
        text = re.sub(r"(?!\s)\W", "", text).lower().strip()
        self.text = text

    def extract_pdf_info(self) -> None:
        """
        Extracts the metadata information of the PDF file if available.
        """
        fp = open(self.full_path, "rb")
        parser = PDFParser(fp)
        doc = PDFDocument(parser)
        info = doc.info
        self._pdf_info = info

    def extract_pdf_text(self) -> None:
        """
        Extract the text from the pdf file.
        """
        doc = fitz.open(self.full_path)
        pages = []
        for page in doc:
            pages += [page.get_text()]
        self._raw_text = pages

    def extract_doi(self) -> None:
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
            first_pages = "\n".join(self._raw_text[0:2])
            doi_list = extract_doi_from_str(first_pages)

        self.doi = doi_list[0] if doi_list else ""

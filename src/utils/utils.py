import re


def extract_doi_from_str(string: str) -> list:
    """Extract all DOIs matches from a string using a regular expression"""
    doi_pattern = r"\b10\.\d{4,}/[-._;()/:a-zA-Z0-9]+\b"
    # Find all matches in the text
    doi_list = re.findall(doi_pattern, string)
    return doi_list


# Microsoft Academic Graph schema
venue_schema = {"id": str, "raw": str}

paper_schema = {
    "id": str,
    "title": str,
    "authors": list[dict],
    "venue": list[dict],
    "year": int,
    "keywords": list[str],
    "n_citation": int,
    "page_start": str,
    "page_end": str,
    "doc_type": str,
    "lang": str,
    "publisher": str,
    "volume": str,
    "issue": str,
    "issn": str,
    "isbn": str,
    "doi": str,
    "pdf": str,
    "url": list,
    "abstract": str,
}

author_schema = {"id": str, "name": str, "org": str}

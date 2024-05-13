class ExistingFileError(Exception):
    """Raised when a file already exists"""


class NotPDFContentError(Exception):
    """Raised when the response content does not match a PDF content's pattern"""


class MissingDOIError(Exception):
    """Raised when the DOI is missing."""


class WrongPaperError(Exception):
    """Raised when there is an error validating the paper content against another source"""

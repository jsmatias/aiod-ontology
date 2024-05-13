class ExistingFileError(Exception):
    """Raised when a file already exists"""


class NotPDFContentError(Exception):
    """Raised when the response content does not match a PDF content's pattern"""

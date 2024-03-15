ENCODE_PATTERN = {".": "_", "/": "-"}


def encode(doi: str, ext: str = "pdf") -> str:

    file_name = doi
    for k, v in ENCODE_PATTERN.items():
        file_name = file_name.replace(k, v)
    file_name = file_name + "." + ext
    return file_name


def decode(file_name: str) -> str:

    doi = file_name.split(".")[0]
    for k, v in ENCODE_PATTERN.items():
        doi = doi.replace(v, k)
    return doi

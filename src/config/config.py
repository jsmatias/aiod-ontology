import configparser
import os
from pathlib import Path, PosixPath


class Config:
    """A simple abstraction layer for the configuration file"""

    def __init__(self) -> None:
        """Initialising the config class"""
        self.dir = Path(os.path.dirname(os.path.realpath(__file__)))
        self.config_file = self.dir / "config.ini"
        self.config = configparser.ConfigParser()
        self.read_config_file()

    # =============================================================================
    #     DATA
    # =============================================================================
    def get_papers_path(self) -> PosixPath:
        """Returns the path where the papers are stored"""
        return Path.resolve(self.dir / self.config["data"]["papers_path"])

    def get_data_path(self) -> PosixPath:
        """Returns the path where the data are stored"""
        return Path.resolve(self.dir / self.config["data"]["data_path"])

    # =============================================================================
    #     METADATA
    # =============================================================================
    def get_metadata_api_url(self) -> str:
        """Returns the url base of the metadata API"""
        return self.config["metadata"]["api_url"]

    def get_metadata_api_headers(self) -> dict:
        """Returns a dictionary with the 'Accept' field of the
        headers to the metadata API get request"""

        headers = {
            "Accept": self.config["metadata"]["headers_accept"]
            + "; "
            + "style="
            + self.config["metadata"]["bibliography_style"]
        }

        return headers

    # =============================================================================
    #     READ AND WRITE CONFIG FILE
    # =============================================================================
    def read_config_file(self) -> None:
        """Reads the config file"""
        self.config.read(self.config_file)

    def write_config_file(self) -> None:
        """Writes the config file"""
        with open(self.config_file, "w", encoding="utf-8") as conf_file:
            self.config.write(conf_file)

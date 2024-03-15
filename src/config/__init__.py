from .config import Config

config = Config()

DATA_PATH = config.get_data_path()
PAPERS_PATH = config.get_papers_path()

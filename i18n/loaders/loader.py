import io
import os.path
from typing import Optional, Dict

from .. import config
from ..errors import I18nFileLoadError


class Loader(object):
    """Base class to load resources"""

    loaded_files: Dict[str, Optional[dict]] = {}

    def __init__(self):
        super(Loader, self).__init__()

    def load_file(self, filename: str) -> str:
        try:
            with io.open(filename, 'r', encoding=config.get('encoding')) as f:
                return f.read()
        except IOError as e:
            raise I18nFileLoadError("error loading file {0}: {1}".format(filename, e.strerror)) from e

    def parse_file(self, file_content: str) -> dict:
        raise NotImplementedError("the method parse_file has not been implemented for class {0}".format(self.__class__.__name__))

    def check_data(self, data: dict, root_data: Optional[str]) -> bool:
        return True if root_data is None else root_data in data

    def get_data(self, data: dict, root_data: Optional[str]) -> dict:
        # use .pop to remove used data from cache
        return data if root_data is None else data.pop(root_data)

    def load_resource(self, filename: str, root_data: Optional[str], remember_content: bool) -> dict:
        filename = os.path.abspath(filename)
        if filename in self.loaded_files:
            data = self.loaded_files[filename]
            if not data:
                # cache is missing or exhausted
                return {}
        else:
            file_content = self.load_file(filename)
            data = self.parse_file(file_content)
        if not self.check_data(data, root_data):
            raise I18nFileLoadError("error getting data from {0}: {1} not defined".format(filename, root_data))
        enable_memoization = config.get('enable_memoization')
        if enable_memoization:
            if remember_content:
                self.loaded_files[filename] = data
            else:
                self.loaded_files[filename] = None
        return self.get_data(data, root_data)

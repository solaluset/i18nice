import os.path
import sys
from importlib import util

from .loader import Loader, I18nFileLoadError


class PythonLoader(Loader):
    """class to load python files"""

    def __init__(self):
        super(PythonLoader, self).__init__()

    def load_file(self, filename):
        _, name = os.path.split(filename)
        module_name, _ = os.path.splitext(name)
        try:
            spec = util.spec_from_file_location(module_name, filename)
            module = util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        except Exception as e:
            raise I18nFileLoadError("error loading file {0}".format(filename)) from e

    def parse_file(self, file_content):
        return file_content

    def check_data(self, data, root_data):
        return hasattr(data, root_data)

    def get_data(self, data, root_data):
        return getattr(data, root_data)

from typing import Type, Union

import yaml
from yaml.loader import __all__ as _known_loaders

from . import Loader, I18nFileLoadError


class YamlLoader(Loader):
    """class to load yaml files"""

    loader: Union[  # type: ignore[valid-type]
        tuple(Type[getattr(yaml, i)] for i in _known_loaders)
    ] = yaml.BaseLoader

    def __init__(self):
        super(YamlLoader, self).__init__()

    def parse_file(self, file_content: str) -> dict:
        try:
            return yaml.load(file_content, Loader=self.loader)
        except yaml.YAMLError as e:
            raise I18nFileLoadError("invalid YAML: {0}".format(str(e))) from e

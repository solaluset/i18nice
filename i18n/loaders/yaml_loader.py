import yaml

from . import Loader, I18nFileLoadError

class YamlLoader(Loader):
    """class to load yaml files"""
    def __init__(self):
        super(YamlLoader, self).__init__()

    def parse_file(self, file_content):
        try:
            if hasattr(yaml, "FullLoader"):
                return yaml.load(file_content, Loader=yaml.FullLoader)
            else:
                return yaml.load(file_content, yaml.Loader)
        except yaml.YAMLError as e:
            raise I18nFileLoadError("invalid YAML: {0}".format(str(e))) from e

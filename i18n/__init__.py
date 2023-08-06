from typing import List

from . import resource_loader
from .resource_loader import (
    Loader,
    register_loader,
    load_config,
    load_everything,
    unload_everything,
    reload_everything,
)
from .errors import (
    I18nException,
    I18nFileLoadError,
    I18nInvalidStaticRef,
    I18nInvalidFormat,
)
from .translator import t
from .translations import add as add_translation
from .custom_functions import add_function
from . import config
from .config import set, get

resource_loader.init_loaders()

load_path: List[str] = config.get("load_path")

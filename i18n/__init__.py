__all__ = (
    "Loader",
    "register_loader",
    "init_default_loaders",
    "load_config",
    "load_everything",
    "unload_everything",
    "reload_everything",

    "I18nException",
    "I18nFileLoadError",
    "I18nInvalidStaticRef",
    "I18nInvalidFormat",

    "t",
    "add_translation",
    "add_function",

    "set",
    "get",

    "load_path",
)

from typing import List

from .resource_loader import (
    Loader,
    register_loader,
    init_loaders as init_default_loaders,
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
from .config import set, get

init_default_loaders()

load_path: List[str] = get("load_path")

del List

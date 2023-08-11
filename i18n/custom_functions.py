from collections import defaultdict
from typing import Optional, Callable, Dict


Function = Callable[..., int]
global_functions: Dict[str, Function] = {}
locales_functions: Dict[str, Dict[str, Function]] = defaultdict(dict)


def add_function(name: str, func: Function, locale: Optional[str] = None) -> None:
    if locale:
        locales_functions[locale][name] = func
    else:
        global_functions[name] = func


def get_function(name: str, locale: Optional[str] = None) -> Optional[Function]:
    if locale and name in locales_functions[locale]:
        return locales_functions[locale][name]
    return global_functions.get(name)

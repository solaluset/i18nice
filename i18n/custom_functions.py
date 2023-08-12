from collections import defaultdict
from typing import Optional, Callable, Dict


Function = Callable[..., int]
global_functions: Dict[str, Function] = {}
locales_functions: Dict[str, Dict[str, Function]] = defaultdict(dict)


def add_function(name: str, func: Function, locale: Optional[str] = None) -> None:
    """
    Adds your function to placeholder functions

    Registers the function to locale functions if locale is given
    or to global (locale-independent) functions otherwise
    The function must accept all kwargs passed to `t` and return an int
    (index that will determine which placeholder argument will be used)

    :param name: Name used to register the function
    :param func: The function to register
    :param locale: Locale to which function will be bound (optional)
    """

    if locale:
        locales_functions[locale][name] = func
    else:
        global_functions[name] = func


def get_function(name: str, locale: Optional[str] = None) -> Optional[Function]:
    if locale and name in locales_functions[locale]:
        return locales_functions[locale][name]
    return global_functions.get(name)

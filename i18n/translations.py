from typing import Optional, Union, List, Dict

from . import config

container = {}


def add(
    key: str,
    value: Union[str, Dict[str, str], List[str], List[Dict[str, str]]],
    locale: Optional[str] = None,
):
    if locale is None:
        locale = config.get('locale')
    container.setdefault(locale, {})[key] = value


def has(key, locale=None):
    if locale is None:
        locale = config.get('locale')
    return key in container.get(locale, {})


def get(key, locale=None):
    if locale is None:
        locale = config.get('locale')
    return container[locale][key]


def clear(locale=None):
    if locale is None:
        container.clear()
    elif locale in container:
        container[locale].clear()

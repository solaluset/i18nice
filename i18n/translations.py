from typing import Optional, Union, List, Dict

from . import config

TranslationType = Union[str, Dict[str, str], List[str], List[Dict[str, str]]]
container: Dict[str, Dict[str, TranslationType]] = {}


def add(
    key: str,
    value: TranslationType,
    locale: Optional[str] = None,
):
    if locale is None:
        locale = config.get('locale')
    container.setdefault(locale, {})[key] = value


def has(key: str, locale: Optional[str] = None) -> bool:
    if locale is None:
        locale = config.get('locale')
    return key in container.get(locale, {})


def get(key: str, locale: Optional[str] = None) -> TranslationType:
    if locale is None:
        locale = config.get('locale')
    return container[locale][key]


def clear(locale: Optional[str] = None):
    if locale is None:
        container.clear()
    elif locale in container:
        container[locale].clear()

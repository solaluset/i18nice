__all__ = ("t",)

from typing import Any, Dict, Union, Tuple, Optional, overload
try:
    from typing import SupportsIndex, Literal
except ImportError:
    SupportsIndex = int  # type: ignore
    Literal = Union

from . import config
from . import resource_loader
from . import translations, formatters


# _list=True indicates that a tuple of translations is expected
# this is purely for type checkers
# it will NOT affect actual return types
@overload
def t(
    key: str,
    *,
    locale: Optional[str] = None,
    _list: Literal[False] = False,
    **kwargs: Any,
) -> str: ...


@overload
def t(
    key: str,
    *,
    locale: Optional[str] = None,
    _list: Literal[True],
    **kwargs: Any,
) -> "LazyTranslationTuple": ...


def t(
    key: str,
    *,
    locale: Optional[str] = None,
    **kwargs: Any,
) -> Union[str, "LazyTranslationTuple"]:
    """
    Main translation function

    Searches for translation in files if it's not already in cache
    Tries fallback locale if search fails and fallback is set
    If that also fails:
      - Returns original key if `on_missing_translation` is not set
      - Raises `KeyError` if it's set to `"error"`
      - Returns result of calling it if it's set to a function

    :param key: Translation key
    :param locale: Locale to translate to (optional)
    :param **kwargs: Keyword arguments used to interpolate placeholders
    (including `count` for pluralization)
    :return: The translation, return value of `on_missing_translation` or the original key
    :raises KeyError: If translation wasn't found and `on_missing_translation` is set to `"error"`
    """

    if not locale:
        locale = config.get("locale")
    locale: str
    try:
        return translate(key, locale, kwargs)
    except KeyError:
        if resource_loader.search_translation(key, locale):
            return translate(key, locale, kwargs)
        fallback = config.get("fallback")
        if fallback and (
            translations.has(key, fallback)
            or resource_loader.search_translation(key, fallback)
        ):
            return translate(key, fallback, kwargs)
    on_missing = config.get('on_missing_translation')
    if on_missing == "error":
        raise KeyError("key {!r} not found for {!r}".format(key, locale))
    elif on_missing:
        return on_missing(key, locale, **kwargs)
    else:
        return key


class LazyTranslationTuple(tuple):
    translation_key: str
    locale: str
    kwargs: dict

    def __new__(
        cls,
        translation_key: str,
        locale: str,
        value: tuple,
        kwargs: dict,
    ) -> "LazyTranslationTuple":
        obj = super().__new__(cls, value)
        obj.translation_key = translation_key
        obj.locale = locale
        obj.kwargs = kwargs
        return obj

    @overload
    def __getitem__(self, key: SupportsIndex) -> str: ...

    @overload
    def __getitem__(self, key: slice) -> Tuple[str, ...]: ...

    def __getitem__(self, key: Union[SupportsIndex, slice]) -> Union[str, Tuple[str, ...]]:
        return formatters.TranslationFormatter(  # type: ignore[return-value]
            self.translation_key,
            self.locale,
            super().__getitem__(key),
            self.kwargs,
        ).format()


def translate(key: str, locale: str, kwargs: Any) -> Union[str, LazyTranslationTuple]:
    translation = translations.get(key, locale)
    if isinstance(translation, tuple):
        return LazyTranslationTuple(key, locale, translation, kwargs)
    else:
        return formatters.TranslationFormatter(
            key, locale, translation, kwargs
        ).format()  # type: ignore[return-value]


def pluralize(key: str, locale: str, translation: Union[Dict[str, str], str], count: int) -> str:
    return_value = key
    try:
        if not isinstance(translation, dict):
            return_value = translation
            raise KeyError('use of count witouth dict for key {0}'.format(key))
        if count == 0:
            if 'zero' in translation:
                return translation['zero']
        elif count == 1:
            if 'one' in translation:
                return translation['one']
        elif count <= config.get('plural_few'):
            if 'few' in translation:
                return translation['few']
        if 'many' in translation:
            return translation['many']
        else:
            raise KeyError('"many" not defined for key {0}'.format(key))
    except KeyError:
        on_missing = config.get('on_missing_plural')
        if on_missing == "error":
            raise
        elif on_missing:
            return on_missing(key, locale, translation, count)
        else:
            return return_value

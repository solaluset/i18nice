__all__ = ("t",)

from typing import Any, Dict, Union, Tuple, Optional, overload
try:
    from typing import SupportsIndex
except ImportError:
    SupportsIndex = int  # type: ignore

from . import config
from . import resource_loader
from . import translations, formatters


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
    try:
        return translate(key, locale=locale, **kwargs)  # type: ignore[arg-type]
    except KeyError:
        resource_loader.search_translation(key, locale)
        if translations.has(key, locale):
            return translate(key, locale=locale, **kwargs)  # type: ignore[arg-type]
        fallback = config.get("fallback")
        if fallback and fallback != locale:
            return t(key, locale=fallback, **kwargs)
    on_missing = config.get('on_missing_translation')
    if on_missing == "error":
        raise KeyError('key {0} not found'.format(key))
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


def translate(key: str, locale: str, **kwargs: Any) -> Union[str, LazyTranslationTuple]:
    translation = translations.get(key, locale=locale)
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

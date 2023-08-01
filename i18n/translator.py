from . import config
from . import resource_loader
from . import translations, formatters


def t(key, **kwargs):
    locale = kwargs.pop('locale', None) or config.get('locale')
    try:
        return translate(key, locale=locale, **kwargs)
    except KeyError:
        resource_loader.search_translation(key, locale)
        if translations.has(key, locale):
            return translate(key, locale=locale, **kwargs)
        elif locale != config.get('fallback'):
            return t(key, locale=config.get('fallback'), **kwargs)
    if 'default' in kwargs:
        return kwargs['default']
    on_missing = config.get('on_missing_translation')
    if on_missing == "error":
        raise KeyError('key {0} not found'.format(key))
    elif on_missing:
        return on_missing(key, locale, **kwargs)
    else:
        return key


class LazyTranslationTuple(tuple):
    def __new__(cls, translation_key, locale, value, kwargs):
        obj = super().__new__(cls, value)
        obj.translation_key = translation_key
        obj.locale = locale
        obj.kwargs = kwargs
        return obj

    def __getitem__(self, key):
        return formatters.TranslationFormatter(
            self.translation_key,
            self.locale,
            super().__getitem__(key),
            self.kwargs,
        ).format()


def translate(key, **kwargs):
    locale = kwargs.pop('locale', None) or config.get('locale')
    translation = translations.get(key, locale=locale)
    if isinstance(translation, tuple):
        return LazyTranslationTuple(key, locale, translation, kwargs)
    else:
        return formatters.TranslationFormatter(key, locale, translation, kwargs).format()


def pluralize(key, locale, translation, count):
    return_value = key
    try:
        if type(translation) != dict:
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

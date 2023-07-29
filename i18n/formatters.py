from re import escape
from string import Template

from . import config, translations
from .errors import I18nInvalidStaticRef
from .custom_functions import get_function


class TranslationFormatter(Template, dict):
    delimiter = config.get("placeholder_delimiter")
    idpattern = r"""
        \w+                      # name
        (
            \(
                [^\(\){}]*       # arguments
            \)
        )?
    """

    def __init__(self, translation_key, template):
        super(TranslationFormatter, self).__init__(template)
        self.translation_key = translation_key

    def format(self, locale, **kwargs):
        self.clear()
        self.update(kwargs)
        self.locale = locale
        if config.get("on_missing_placeholder"):
            return self.substitute(self)
        else:
            return self.safe_substitute(self)

    def __getitem__(self, key: str):
        try:
            name, _, args = key.partition("(")
            if args:
                f = get_function(name, self.locale)
                if f:
                    i = f(**self)
                    args = args.strip(")").split(config.get("argument_delimiter"))
                    try:
                        return args[i]
                    except (IndexError, TypeError) as e:
                        raise ValueError(
                            "No argument {0!r} for function {1!r} (in {2!r})".format(
                                i, name, self.template
                            )
                        ) from e
                raise KeyError(
                    "No function {0!r} found for locale {1!r} (in {2!r})".format(
                        name, self.locale, self.template
                    )
                )
            return super().__getitem__(key)
        except KeyError:
            on_missing = config.get("on_missing_placeholder")
            if not on_missing or on_missing == "error":
                raise
            return on_missing(self.translation_key, self.locale, self.template, key)


class StaticFormatter(Template):
    delimiter = config.get("placeholder_delimiter")
    idpattern = r"""
        ({})
        |
        ({}\w+)+
    """.format(
        TranslationFormatter.idpattern,
        escape(config.get("namespace_delimiter")),
    )

    def __init__(self, locale, translation_key, template):
        super().__init__(template)
        self.locale = locale
        self.path = translation_key.split(config.get("namespace_delimiter"))

    def format(self):
        result = self.safe_substitute(self)
        # keep substituting in case of nested references
        # python will throw an exception if there's a recursive reference
        if result != self.template:
            self.template = result
            return self.format()
        return result

    def __getitem__(self, key: str):
        delim = config.get("namespace_delimiter")
        full_key = key.lstrip(delim)
        if full_key == key:
            # not a static reference, skip
            raise KeyError()
        for i in range(1, len(self.path) + 1):
            try:
                return translations.get(full_key, self.locale)
            except KeyError:
                full_key = delim.join(self.path[:i]) + key
        raise I18nInvalidStaticRef(
            "no value found for static reference {!r} (in {!r})"
            .format(key, delim.join(self.path)),
        )

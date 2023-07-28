from string import Template

from . import config
from .custom_functions import get_function


_formatters = set()

def reload():
    for f in _formatters:
        f.reload()


class BaseFormatter(Template):
    def __init_subclass__(cls):
        _formatters.add(cls)
        super().__init_subclass__()

    @classmethod
    def reload(cls):
        cls.delimiter = config.get("placeholder_delimiter")
        # hacky trick to reload formatter's configuration
        del cls.pattern
        cls.__init_subclass__()


class TranslationFormatter(BaseFormatter, dict):
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


reload()

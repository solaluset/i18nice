from re import compile, escape
from string import Template, Formatter as _Fmt

from . import config, translations
from .translator import pluralize
from .errors import I18nInvalidStaticRef, I18nInvalidFormat
from .custom_functions import get_function


class Formatter(Template):
    delimiter = config.get("placeholder_delimiter")

    def __init__(self, translation_key, locale, value, kwargs):
        super().__init__(value)
        self.translation_key = translation_key
        self.locale = locale
        self.kwargs = kwargs

    def substitute(self):
        return super().substitute(self)

    def safe_substitute(self):
        return super().safe_substitute(self)

    def _format_str(self):
        raise NotImplementedError

    def format(self):
        if isinstance(self.template, str):
            return self._format_str()
        if isinstance(self.template, dict):
            result = {}
            for k, v in self.template.items():
                self.template = v
                result[k] = self.format()
            return result
        # assuming list/tuple
        result = []
        for v in self.template:
            self.template = v
            result.append(self.format())
        return tuple(result)

    def __getitem__(self, key: str):
        return self.kwargs[key]


class TranslationFormatter(Formatter):
    idpattern = r"""
        \w+                      # name
        (
            \(
                [^\(\){}]*       # arguments
            \)
        )?
    """

    def __init__(self, translation_key, locale, value, kwargs):
        super().__init__(translation_key, locale, value, kwargs)
        self.pluralized = False

    def format(self):
        if not self.pluralized and "count" in self.kwargs:
            if isinstance(self.template, tuple):
                self.template = tuple(
                    pluralize(
                        self.translation_key,
                        self.locale,
                        i,
                        self.kwargs["count"],
                    )
                    for i in self.template
                )
            else:
                self.template = pluralize(
                    self.translation_key,
                    self.locale,
                    self.template,
                    self.kwargs["count"],
                )
            self.pluralized = True
        return super().format()

    def _format_str(self):
        if config.get("on_missing_placeholder"):
            return self.substitute()
        else:
            return self.safe_substitute()

    def __getitem__(self, key: str):
        try:
            name, _, args = key.partition("(")
            if args:
                f = get_function(name, self.locale)
                if f:
                    i = f(**self.kwargs)
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


class StaticFormatter(Formatter):
    idpattern = r"""
        ({})
        |
        ({}\w+)+
    """.format(
        TranslationFormatter.idpattern,
        escape(config.get("namespace_delimiter")),
    )

    def __init__(self, translation_key, locale, value):
        super().__init__(translation_key, locale, value, None)
        self.path = translation_key.split(config.get("namespace_delimiter"))

    def _format_str(self):
        return self.safe_substitute()

    def __getitem__(self, key: str):
        delim = config.get("namespace_delimiter")
        full_key = key.lstrip(delim)
        if full_key == key:
            # not a static reference, skip
            raise KeyError()

        for i in range(1, len(self.path) + 1):
            try:
                # keep expanding in case of nested references
                # python will throw an exception if there's a recursive reference
                expand_static_refs((full_key,), self.locale)
                return translations.get(full_key, self.locale)
            except KeyError:
                full_key = delim.join(self.path[:i]) + key

        # try to search in other files
        from .resource_loader import search_translation

        full_key = key.lstrip(delim)
        search_translation(full_key, self.locale)
        try:
            return translations.get(full_key, self.locale)
        except KeyError:
            raise I18nInvalidStaticRef(
                "no value found for static reference {!r} (in {!r})"
                .format(key, self.translation_key),
            )


def expand_static_refs(keys, locale):
    for key in keys:
        tr = translations.get(key, locale)
        tr = StaticFormatter(key, locale, tr).format()
        translations.add(key, tr, locale)


class FilenameFormat(_Fmt):
    def __init__(self, template: str, variables: dict):
        super().__init__()
        self.template = template
        self.variables = variables
        self.used_variables = set()
        self.pattern = compile(super().format(template))

    @property
    def format(self):
        return self.template.format

    @property
    def match(self):
        return self.pattern.fullmatch

    def __getattr__(self, name: str):
        if name.startswith("has_"):
            _, _, var_name = name.partition("_")
            if var_name in self.variables:
                return var_name in self.used_variables
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")

    def parse(self, s):
        for text, field, spec, conversion in super().parse(s):
            if spec or conversion:
                raise I18nInvalidFormat("Can't apply format spec or conversion in filename format")
            text = escape(text)
            if field is not None:
                try:
                    text += f"(?P<{field}>{self.variables[field]})"
                except KeyError as e:
                    raise I18nInvalidFormat(f"Unknown placeholder in filename format: {e}") from e
                self.used_variables.add(field)
            yield text, None, None, None

    def __repr__(self):
        return f"{self.__class__.__name__}({self.template!r}, {self.variables!r})"

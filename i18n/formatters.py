__all__ = ("TranslationFormatter", "StaticFormatter", "FilenameFormat", "expand_static_refs")

from re import Match, compile, escape
from string import Template, Formatter as _Fmt
from typing import Any, Iterable, Optional, Set, Callable, Tuple, TypeVar, NoReturn
from collections.abc import Mapping

from . import config, translations
from .translations import TranslationType
from .translator import pluralize
from .errors import I18nInvalidStaticRef, I18nInvalidFormat
from .custom_functions import get_function


if config.get("namespace_delimiter") != "-":
    _name_pattern = r"(\w|-)+"
else:
    _name_pattern = r"\w+"


class Formatter(
    Template,
    Mapping,
    metaclass=type(  # type: ignore[misc]
        "FormatterMeta",
        tuple(c for c in map(type, (Template, Mapping)) if c != type),
        {},
    ),
):
    delimiter = config.get("placeholder_delimiter")

    # for mypy
    _invalid: Callable[[Match], NoReturn]

    def __init__(self, translation_key: str, locale: str, value: TranslationType, kwargs: dict):
        super().__init__(value)  # type: ignore[arg-type]
        self.translation_key = translation_key
        self.locale = locale
        self.kwargs = kwargs

    def substitute(self, static: bool = False) -> str:  # type: ignore[override]
        def convert(mo):
            named = mo.group("named") or mo.group("braced")
            if named is not None:
                try:
                    return str(self[named])
                except KeyError:
                    on_missing = config.get("on_missing_placeholder")
                    if not on_missing:
                        return mo.group()
                    if on_missing == "error":
                        raise
                    return on_missing(self.translation_key, self.locale, self.template, named)
            if mo.group("escaped") is not None:
                return self.delimiter if not static else mo.group()
            if mo.group("invalid") is not None:  # pragma: no branch
                if not static:
                    self._invalid(mo)
                else:
                    return mo.group()
            assert False, "Something went wrong. Please report this bug."  # pragma: no cover
        return self.pattern.sub(convert, self.template)

    def safe_substitute(self) -> str:  # type: ignore[override]
        raise NotImplementedError("This isn't supposed to be called!")

    def _format_str(self) -> str:
        raise NotImplementedError

    def format(self) -> TranslationType:
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

    def __getitem__(self, key: str) -> Any:
        return self.kwargs[key]

    def __len__(self):
        return self.kwargs.__len__()

    def __iter__(self):
        return self.kwargs.__iter__()


class WrappedException(Exception):
    pass


class TranslationFormatter(Formatter):
    idpattern = fr"""
        {_name_pattern}          # name
        (
            \(
                [^\(\)]*         # arguments
            \)
        )?
    """

    def __init__(self, translation_key: str, locale: str, value: TranslationType, kwargs: dict):
        super().__init__(translation_key, locale, value, kwargs)
        self.pluralized = False

    def format(self) -> TranslationType:
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

    def _format_str(self) -> str:
        try:
            return self.substitute()
        except WrappedException as e:
            # unwrap
            raise e.args[0] from None

    def __getitem__(self, key: str) -> Any:
        name, _, args = key.partition("(")
        if args:
            f = get_function(name, self.locale)
            if f:
                args = args.strip(")")
                if args:
                    arg_list = args.split(config.get("argument_delimiter"))
                else:
                    arg_list = []
                try:
                    return f(*arg_list, **self.kwargs)
                except KeyError as e:
                    # wrap KeyError from user's function
                    # to avoid treating it as missing placeholder
                    raise WrappedException(e)
            raise KeyError(
                "No function {0!r} found for locale {1!r} (in {2!r})".format(
                    name, self.locale, self.template
                )
            )
        return super().__getitem__(key)


class StaticFormatter(Formatter):
    idpattern = r"""
        ({}{})+
    """.format(
        escape(config.get("namespace_delimiter")),
        _name_pattern,
    )

    def __init__(self, translation_key: str, locale: str, value: TranslationType):
        super().__init__(translation_key, locale, value, {})
        self.path = translation_key.split(config.get("namespace_delimiter"))

    def _format_str(self) -> str:
        return self.substitute(static=True)

    def __getitem__(self, key: str) -> Any:
        delim = config.get("namespace_delimiter")
        full_key = key.lstrip(delim)

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
        if search_translation(full_key, self.locale):
            return translations.get(full_key, self.locale)
        raise I18nInvalidStaticRef(
            "no value found for static reference {!r} (in {!r})"
            .format(key, self.translation_key),
        )


def expand_static_refs(keys: Iterable[str], locale: str) -> None:
    for key in keys:
        tr = translations.get(key, locale)
        tr = StaticFormatter(key, locale, tr).format()
        translations.add(key, tr, locale)


# This is (hopefully) a temporary workaround
# https://github.com/python/mypy/issues/15848
StrOrLiteralStr = TypeVar("StrOrLiteralStr", str, str)


class FilenameFormat(_Fmt):
    def __init__(self, template: str, variables: dict):
        super().__init__()
        self.template = template
        self.variables = variables
        self.used_variables: Set[str] = set()
        self.pattern = compile(super().format(template))

    @property
    def format(self) -> Callable[..., str]:
        return self.template.format

    @property
    def match(self) -> Callable[[str], Optional[Match]]:
        return self.pattern.fullmatch

    def __getattr__(self, name: str) -> bool:
        if name.startswith("has_"):
            _, _, var_name = name.partition("_")
            if var_name in self.variables:
                return var_name in self.used_variables
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")

    def parse(self, s: StrOrLiteralStr) -> Iterable[Tuple[StrOrLiteralStr, None, None, None]]:
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

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.template!r}, {self.variables!r})"

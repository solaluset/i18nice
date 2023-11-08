__all__ = (
    "Loader",
    "register_loader",
    "init_loaders",
    "load_config",
    "load_everything",
    "unload_everything",
    "reload_everything",
    "search_translation",
)

import os.path
from typing import Type, Iterable, Optional, List, Set, Union

from . import config
from .loaders import Loader, I18nFileLoadError
from .errors import I18nLockedError
from . import translations, formatters

loaders = {}

PLURALS = {"zero", "one", "few", "many"}


def register_loader(loader_class: Type[Loader], supported_extensions: Iterable[str]) -> None:
    """
    Registers loader for files

    :param loader_class: Loader to register
    :param supported_extensions: Iterable of file extensions that the loader supports
    :raises ValueError: If `loader_class` is not a subclass of `i18n.Loader`
    """

    if not issubclass(loader_class, Loader):
        raise ValueError("loader class should be subclass of i18n.Loader")

    loader = loader_class()
    for extension in supported_extensions:
        loaders[extension] = loader


def load_resource(filename: str, root_data: Optional[str], remember_content: bool = False) -> dict:
    extension = os.path.splitext(filename)[1][1:]
    if extension not in loaders:
        raise I18nFileLoadError("no loader available for extension {0}".format(extension))
    return loaders[extension].load_resource(filename, root_data, remember_content)


def init_loaders():
    """Sets default loaders"""

    init_python_loader()
    if config.yaml_available:
        init_yaml_loader()
    if config.json_available:
        init_json_loader()


def init_python_loader():
    from .loaders import PythonLoader
    register_loader(PythonLoader, ["py"])


def init_yaml_loader():
    from .loaders import YamlLoader
    register_loader(YamlLoader, ["yml", "yaml"])


def init_json_loader():
    from .loaders import JsonLoader
    register_loader(JsonLoader, ["json"])


def load_config(filename: str) -> None:
    """
    Loads configuration from file

    :param filename: File containing configuration
    """

    settings_data = load_resource(filename, "settings")
    for key, value in settings_data.items():
        config.set(key, value)


def get_namespace_from_filepath(filename: str) -> str:
    namespace = os.path.dirname(filename).strip(os.sep).replace(
        os.sep,
        config.get("namespace_delimiter"),
    )
    format = config.get('filename_format')
    if format.has_namespace:
        filename_match = format.match(os.path.basename(filename))
        if namespace:
            namespace += config.get('namespace_delimiter')
        namespace += filename_match.group("namespace")
    return namespace


def load_translation_file(filename: str, base_directory: str, locale: Optional[str] = None) -> None:
    if locale is None:
        locale = config.get('locale')
    skip_locale_root_data = config.get('skip_locale_root_data')
    root_data = None if skip_locale_root_data else locale
    # if the file isn't dedicated to one locale and may contain other `root_data`s
    remember_content = not config.get("filename_format").has_locale and root_data
    translations_dic = load_resource(
        os.path.join(base_directory, filename),
        root_data,
        bool(remember_content),
    )
    namespace = get_namespace_from_filepath(filename)
    loaded = load_translation_dic(translations_dic, namespace, locale)
    formatters.expand_static_refs(loaded, locale)


_locked: Union[bool, Set[Union[str, None]]] = False


def _check_locked(locale: Optional[str]) -> bool:
    return _locked if isinstance(_locked, bool) else locale in _locked


def load_everything(locale: Optional[str] = None, *, lock: bool = False) -> None:
    """
    Loads all translations

    If locale is provided, loads translations only for that locale

    :param locale: Locale (optional)
    :param lock: Whether to lock translations after loading.
    Locking disables further searching for missing translations
    """

    global _locked

    if _check_locked(locale):
        raise I18nLockedError("Translations were locked, use unload_everything() to unlock")

    for directory in config.get("load_path"):
        if config.get("use_locale_dirs"):
            for locale_dir in os.listdir(directory):
                if locale and locale_dir != locale:
                    continue
                locale_dir_path = os.path.join(directory, locale_dir)
                if not os.path.isdir(locale_dir_path):
                    continue
                recursive_load_everything(locale_dir_path, "", locale_dir)
        else:
            recursive_load_everything(directory, "", locale)

    if not lock:
        return

    if locale:
        if isinstance(_locked, bool):
            _locked = {None, locale}
        else:
            _locked.add(locale)
    else:
        _locked = True


def unload_everything():
    """Clears all cached translations"""

    global _locked

    translations.clear()
    Loader.loaded_files.clear()
    _locked = False


def reload_everything(*, lock: bool = False) -> None:
    """
    Shortcut for `unload_everything()` + `load_everything()`

    :param lock: Passed to `load_everything()`, see its description for more information
    """

    unload_everything()
    load_everything(lock=lock)


def load_translation_dic(dic: dict, namespace: str, locale: str) -> Iterable[str]:
    loaded: List[str] = []
    if namespace:
        namespace += config.get('namespace_delimiter')
    for key, value in dic.items():
        full_key = namespace + key
        if isinstance(value, dict) and len(PLURALS.intersection(value)) < 2:
            loaded.extend(load_translation_dic(value, full_key, locale))
        else:
            translations.add(full_key, value, locale)
            loaded.append(full_key)
    return loaded


def search_translation(key: str, locale: str) -> bool:
    if not _check_locked(locale):
        splitted_key = key.split(config.get('namespace_delimiter'))
        namespace = splitted_key[:-1]
        for directory in config.get("load_path"):
            if config.get("use_locale_dirs"):
                directory = os.path.join(directory, locale)
            recursive_search_dir(namespace, "", directory, locale)
    return translations.has(key, locale)


def recursive_search_dir(
    splitted_namespace: List[str],
    directory: str,
    root_dir: str,
    locale: str,
) -> None:
    namespace = splitted_namespace[0] if splitted_namespace else ""
    seeked_file = os.path.join(
        directory,
        config.get("filename_format").format(
            namespace=namespace,
            locale=locale,
            format=config.get("file_format"),
        ),
    )
    if os.path.isfile(os.path.join(root_dir, seeked_file)):
        return load_translation_file(seeked_file, root_dir, locale)

    if not namespace:
        return
    namespace = os.path.join(directory, namespace)
    if os.path.isdir(os.path.join(root_dir, namespace)):
        recursive_search_dir(
            splitted_namespace[1:],
            namespace,
            root_dir,
            locale,
        )


def recursive_load_everything(root_dir: str, directory: str, locale: Optional[str]) -> None:
    dir_ = os.path.join(root_dir, directory)
    for f in os.listdir(dir_):
        path = os.path.join(dir_, f)
        if os.path.isfile(path):
            if os.path.splitext(path)[1][1:] != config.get("file_format"):
                continue
            format_match = config.get("filename_format").match(f)
            if not format_match:
                continue
            requested_locale = locale
            file_locale = format_match.groupdict().get("locale", requested_locale)
            if requested_locale is None:
                requested_locale = file_locale
            if requested_locale is not None:
                if requested_locale == file_locale:
                    load_translation_file(
                        os.path.join(directory, f),
                        root_dir,
                        requested_locale,
                    )
            elif not config.get("skip_locale_root_data"):
                file_content = load_resource(path, None, False)
                for loc, dic in file_content.items():
                    if isinstance(dic, dict):
                        loaded = load_translation_dic(
                            dic,
                            get_namespace_from_filepath(os.path.join(directory, f)),
                            loc,
                        )
                        formatters.expand_static_refs(loaded, loc)
            else:
                raise I18nFileLoadError(
                    f"Cannot identify locales for {path!r}:"
                    " filename_format doesn't include locale"
                    " and skip_locale_root_data is set to True"
                )
        elif os.path.isdir(path):  # pragma: no branch
            recursive_load_everything(
                root_dir,
                os.path.join(directory, f),
                locale,
            )

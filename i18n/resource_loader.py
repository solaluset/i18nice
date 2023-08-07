import os.path
from typing import Type, Iterable, Optional

from . import config
from .loaders import Loader, I18nFileLoadError
from . import translations, formatters

loaders = {}

PLURALS = {"zero", "one", "few", "many"}


def register_loader(loader_class: Type[Loader], supported_extensions: Iterable[str]):
    if not issubclass(loader_class, Loader):
        raise ValueError("loader class should be subclass of i18n.Loader")

    loader = loader_class()
    for extension in supported_extensions:
        loaders[extension] = loader


def load_resource(filename, root_data, remember_content=False):
    extension = os.path.splitext(filename)[1][1:]
    if extension not in loaders:
        raise I18nFileLoadError("no loader available for extension {0}".format(extension))
    return loaders[extension].load_resource(filename, root_data, remember_content)


def init_loaders():
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


def load_config(filename: str):
    settings_data = load_resource(filename, "settings")
    for key, value in settings_data.items():
        config.set(key, value)


def get_namespace_from_filepath(filename):
    namespace = os.path.dirname(filename).strip(os.sep).replace(os.sep, config.get('namespace_delimiter'))
    format = config.get('filename_format')
    if format.has_namespace:
        filename_match = format.match(os.path.basename(filename))
        if namespace:
            namespace += config.get('namespace_delimiter')
        namespace += filename_match.group("namespace")
    return namespace


def load_translation_file(filename, base_directory, locale=None):
    if locale is None:
        locale = config.get('locale')
    skip_locale_root_data = config.get('skip_locale_root_data')
    root_data = None if skip_locale_root_data else locale
    # if the file isn't dedicated to one locale and may contain other `root_data`s
    remember_content = not config.get("filename_format").has_locale and root_data
    translations_dic = load_resource(os.path.join(base_directory, filename), root_data, remember_content)
    namespace = get_namespace_from_filepath(filename)
    loaded = load_translation_dic(translations_dic, namespace, locale)
    formatters.expand_static_refs(loaded, locale)


def load_everything(locale: Optional[str] = None):
    for directory in config.get("load_path"):
        recursive_load_everything(directory, "", locale)


def unload_everything():
    translations.clear()
    Loader.loaded_files.clear()


def reload_everything():
    unload_everything()
    load_everything()


def load_translation_dic(dic, namespace, locale):
    loaded = []
    if namespace:
        namespace += config.get('namespace_delimiter')
    for key, value in dic.items():
        full_key = namespace + key
        if type(value) == dict and len(PLURALS.intersection(value)) < 2:
            loaded.extend(load_translation_dic(value, full_key, locale))
        else:
            translations.add(full_key, value, locale)
            loaded.append(full_key)
    return loaded


def search_translation(key, locale=None):
    if locale is None:
        locale = config.get('locale')
    splitted_key = key.split(config.get('namespace_delimiter'))
    namespace = splitted_key[:-1]
    for directory in config.get("load_path"):
        recursive_search_dir(namespace, "", directory, locale)


def recursive_search_dir(splitted_namespace, directory, root_dir, locale):
    namespace = splitted_namespace[0] if splitted_namespace else ""
    seeked_file = config.get('filename_format').format(namespace=namespace, format=config.get('file_format'), locale=locale)
    dir_content = os.listdir(os.path.join(root_dir, directory))
    if seeked_file in dir_content:
        load_translation_file(os.path.join(directory, seeked_file), root_dir, locale)
    elif namespace in dir_content:
        recursive_search_dir(splitted_namespace[1:], os.path.join(directory, namespace), root_dir, locale)


def recursive_load_everything(root_dir, directory, locale):
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
                for l, dic in file_content.items():
                    if isinstance(dic, dict):
                        load_translation_dic(
                            dic,
                            get_namespace_from_filepath(os.path.join(directory, f)),
                            l,
                        )
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

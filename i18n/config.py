from importlib import reload as _reload

try:
    __import__("yaml")
    yaml_available = True
except ImportError:
    yaml_available = False

try:
    __import__("json")
    json_available = True
except ImportError:
    json_available = False

# try to get existing path object
# in case if config is being reloaded
try:
    from . import load_path
    load_path.clear()
except ImportError:
    load_path = []


FILENAME_VARS = dict.fromkeys(
    ("namespace", "locale", "format"),
    r"\w+",
)


settings = {
    'filename_format': '{namespace}.{locale}.{format}',
    'file_format': 'yml' if yaml_available else 'json' if json_available else 'py',
    'available_locales': ['en'],
    'load_path': load_path,
    'locale': 'en',
    'fallback': 'en',
    'placeholder_delimiter': '%',
    'on_missing_translation': None,
    'on_missing_placeholder': None,
    'on_missing_plural': None,
    'encoding': 'utf-8',
    'namespace_delimiter': '.',
    'plural_few': 5,
    'skip_locale_root_data': False,
    'enable_memoization': False,
    'argument_delimiter': '|'
}

def set(key, value):
    if key not in settings:
        raise KeyError("Invalid setting: {0}".format(key))
    elif key == 'load_path':
        load_path.clear()
        load_path.extend(value)
        return
    elif key == 'filename_format':
        from .formatters import FilenameFormat

        value = FilenameFormat(value, FILENAME_VARS)

    settings[key] = value

    if key in ('placeholder_delimiter', 'namespace_delimiter'):
        from . import formatters

        _reload(formatters)

def get(key):
    return settings[key]


# initialize FilenameFormat
set('filename_format', get('filename_format'))

# i18nice [![tests](https://github.com/solaluset/i18nice/actions/workflows/ci.yml/badge.svg)](https://github.com/solaluset/i18nice/actions/workflows/ci.yml) [![Coverage Status](https://coveralls.io/repos/github/solaluset/i18nice/badge.svg)](https://coveralls.io/github/solaluset/i18nice) [![pypi badge](https://img.shields.io/pypi/v/i18nice.svg)](https://pypi.org/project/i18nice/) [![Anaconda-Server Badge](https://anaconda.org/conda-forge/i18nice/badges/version.svg)](https://anaconda.org/conda-forge/i18nice)

This library provides i18n functionality for Python 3 out of the box. The usage is mostly based on Rails i18n library.

[CHANGELOG](CHANGELOG.md)

[CONTRIBUTING](CONTRIBUTING.md)

## Installation

Just run

```shell
pip install i18nice
```

If you want to use YAML to store your translations, use

```shell
pip install i18nice[YAML]
```

## Usage
### Basic usage

The simplest, though not very useful usage would be

```python
import i18n
i18n.add_translation('foo', 'bar')
i18n.t('foo') # bar
```

### Using translation files

YAML and JSON formats are supported to store translations. With the default configuration, if you have the following `foo.en.yml` file

```yaml
en:
  hi: Hello world !
```

Or a JSON file `foo.en.json`

```json
{
  "en": {
    "hi": "Hello world !"
  }
}
```

in `/path/to/translations` folder, you simply need to add the folder to the translations path.

```python
import i18n
i18n.load_path.append('/path/to/translations')
i18n.t('foo.hi') # Hello world !
```

Please note that YAML format is used as default file format if you have `yaml` module installed.
If both `yaml` and `json` modules available and you want to use JSON to store translations, explicitly specify that: `i18n.set('file_format', 'json')`

**!WARNING!**
`yaml.FullLoader` is no longer used by default.
If you need full yaml functionalities, override it with a custom loader:

```python
class MyLoader(i18n.loaders.YamlLoader):
    loader = yaml.FullLoader

i18n.register_loader(MyLoader, ["yml", "yaml"])
```

### Memoization

The configuration value `enable_memoization` (`True` by default) disables reloading of files every time when searching for missing translation.
When translations are loaded, they're always stored in memory, hence it does not affect how existing translations are accessed.

### Load everything

`i18n.load_everything()` will load every file in `load_path` and subdirectories that matches `filename_format` and `file_format`.
You can call it with locale argument to load only one locale.

`i18n.unload_everything()` will clear all caches.

`i18n.reload_everything()` is just a shortcut for `unload_everything()` followed by `load_everything()`.

For the best performance, you can pass `lock=True` to `load_everything()` to disable searching for missing translations completely.
It'll prevent slowdowns caused by missing translations, but you'll need to use `unload_everything()` to be able to load files again.

### Namespaces

#### File namespaces
In the above example, the translation key is `foo.hi` and not just `hi`. This is because the translation filename format is by default `{namespace}.{locale}.{format}`, so the {namespace} part of the file is used as translation.

To remove `{namespace}` from filename format please change the `filename_format` configuration.

```python
i18n.set('filename_format', '{locale}.{format}')
```

#### Directory namespaces
If your files are in subfolders, the foldernames are also used as namespaces, so for example if your translation root path is `/path/to/translations` and you have the file `/path/to/translations/my/app/name/foo.en.yml`, the translation namespace for the file will be `my.app.name` and the file keys will therefore be accessible from `my.app.name.foo.my_key`.

## Functionalities
### Placeholder

You can of course use placeholders in your translations. With the default configuration, the placeholders are used by inserting `%{placeholder_name}` in the translation string. Here is a sample usage.

```python
i18n.add_translation('hi', 'Hello %{name} !')
i18n.t('hi', name='Bob') # Hello Bob !
```

Braces are optional if the identifier is separated from following words.

To escape the delimiter you need to put it twice (like `%%`).

### Pluralization

Pluralization is based on Rail i18n module. By passing a `count` variable to your translation, it will be pluralized. The translation value should be a dictionary with at least the keys `one` and `many`. You can add a `zero` or `few` key when needed, if it is not present `many` will be used instead. Here is a sample usage.

```python
i18n.add_translation('mail_number', {
    'zero': 'You do not have any mail.',
    'one': 'You have a new mail.',
    'few': 'You only have %{count} mails.',
    'many': 'You have %{count} new mails.'
})
i18n.t('mail_number', count=0) # You do not have any mail.
i18n.t('mail_number', count=1) # You have a new mail.
i18n.t('mail_number', count=3) # You only have 3 new mails.
i18n.t('mail_number', count=12) # You have 12 new mails.
```

### Fallback

You can set a fallback which will be used when the key is not found in the default locale.

```python
i18n.set('locale', 'jp')
i18n.set('fallback', 'en')
i18n.add_translation('foo', 'bar', locale='en')
i18n.t('foo') # bar
```

Note that setting `locale` and `fallback` to the same value will result in `fallback` being `None`.

### Skip locale from root
Sometimes i18n structure file came from another project or not contains root element with locale eg. `en` name.

```json
{
  "foo": "FooBar"
}
```

However, we would like to use this i18n .json file in our Python sub-project or micro service as base file for translations.
`i18nice` has special configuration that is skipping locale eg. `en` root data element from the file.

```python
i18n.set('skip_locale_root_data', True)
```

### Different directory structure
If your tree of translation files looks similar to this, you can enable `use_locale_dirs` to get the files properly loaded:

```
locales
├── en-US
│   ├── common.yml
│   └── gui
│       ├── page1.yml
│       └── page2.yml
└── fr-FR
    ├── common.yml
    └── gui
        ├── page1.yml
        └── page2.yml
```

Example code:

```python
import i18n

i18n.load_path.append("locales")
i18n.set("file_format", "yml")
i18n.set("filename_format", "{namespace}.{format}")
i18n.set("skip_locale_root_data", True)
i18n.set("use_locale_dirs", True)

print(i18n.t("common.text1", locale="en-US"))
print(i18n.t("gui.page1.title", locale="en-US"))
```

### Lists

It's possible to use lists of translations, for example:

```yaml
# translations.en.yml
en:
  days:
    - Monday
    - Tuesday
    - Wednesday
    ...
```

```python
# translate.py
from datetime import date
import i18n

i18n.load_path.append(".")
# will print current day
print(i18n.t("translations.days")[date.today().weekday()])
```

It's also possible to use pluralization in lists:

```yml
days:
  - one: Monday
    many: Mondays
  ...
```

Note 1:
The function actually returns a `LazyTranslationTuple` instead of `list`.

Note 2:
Because the tuple is lazy, it'll only process elements when they're requested.
If you need to get fully processed translation, you can force it with `[:]`:

```python
# ({'one': 'Monday', 'many': 'Mondays'}, {'one': 'Tuesday', 'many': 'Tuesdays'}, ...)
print(i18n.t("translations.days", count=3))
# ('Mondays', 'Tuesdays', 'Wednesdays')
print(i18n.t("translations.days", count=3)[:])
```

Note 3 (for type checking):
`t` declares its return type as `str` by default. To simplify type checking in situations where lists are used, you can pass `_list=True` to it, which should have less overhead than calling `cast` and be less intrusive than `type: ignore` comment.
**This will NOT affect actual return type and is purely for type checkers.**

### Static references

Static references allow you to refer to other translation values. This can be useful to avoid repetition. To create a static reference, simply put a key prefixed with namespace delimiter to a placeholder. For example:

```json
{
  "en": {
    "progname": "Program Name",
    "welcome": "Welcome to %{.progname}!"
  }
}
```

Note that you don't need to specify the absolute key:

```json
{
  "en": {
    "interface": {
      "progname": "Program Name",
      "ref": "%{.progname} and %{.interface.progname} refer to the same value"
    }
  }
}
```

To be exact, keys are searched from top to bottom. For example, if you referred to `.c.my_key` in `a.b.c.d`, the library will first check for `c.my_key`, then `a.c.my_key`, and finally find `a.b.c.my_key` if it's present. If not, it'll try to search `c.my_key` in other files and throw an exception if that also fails.

### Error handling

There are three config options for handling different situations.
Setting it to `None` disables handling (default), `"error"` enables error throwing.
You can also set your custom handlers:

`on_missing_translation(key, locale, **kwargs)`

`on_missing_plural(key, locale, translation, count)`

`on_missing_placeholder(key, locale, translation, placeholder)`

Example:

```python
import logging, i18n

def handler(key, locale, text, name):
    logging.warning(f"Missing placeholder {name!r} while translating {key!r} to {locale!r} (in {text!r})")
    return "undefined"

i18n.set("on_missing_placeholder", handler)
i18n.add_translation("am", "Amount is %{amount}")
print(i18n.t("am"))
# output:
# WARNING:root:Missing placeholder 'amount' while translating 'am' to 'en' (in 'Amount is %{amount}')
# Amount is undefined
```

### Custom functions

Add your custom functions and choose translation variants during runtime.

The function should accept as many positional arguments as there are values specified between brackets.
All keyword arguments given to `t` will be passed to the function.
The call in translation will be substituted with the return value.

This may be an alternative for pluralization, especially if a language has more than one plural form.

Example (correct plural form of days in Ukrainian):

```python
i18n.set("locale", "uk")
i18n.add_translation("days", "%{count} %{p(день|дні|днів)}")

def determine_plural_form(*args, count, **_):
    count = abs(count)
    if count % 10 >= 5 or count % 10 == 0 or (count % 100) in range(11, 20):
        return args[2]
    elif count % 10 == 1:
        return args[0]
    return args[1]

i18n.add_function("p", determine_plural_form, "uk")
i18n.t("days", count=1) # 1 день
i18n.t("days", count=2) # 2 дні
i18n.t("days", count=5) # 5 днів
```

## Development

### Setup
You can setup the development virtual environment by `python dev-helper.py`.
It also runs tests and code quality checks.

You can create git pre-commit hook by `python dev-helper.py install`.

### Testing
You can run tests with `python dev-helper.py run-tests`.

### Code Quality Checking
You can run code quality checks with `python dev-helper.py run-checks`.

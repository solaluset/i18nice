## Note: **(B)** = BREAKING, (pb) = potentially breaking

### Hint: use `https://github.com/solaluset/i18nice/compare/v<version 1 (older)>...v<version 2 (newer)>` to see full code difference between versions

### v0.15.3
- Locale can now be passed as positional argument

### v0.15.2
- (pb) A dict will be considered plural only if all keys are plurals

### v0.15.1
- (pb) Positional arguments will not be passed to functions that don't have anything between brackets

### v0.15.0
- **(B)** Changed custom functions again. Now it is `lambda *a, **kw: a[kw["count"] != 1]`.

### v0.14.1
- Updated README

### v0.14.0
- **(B)** Changed custom functions interface. If you've used them, you basically need to change `lambda **kw: kw["count"] != 1` to `lambda a, **kw: a[kw["count"] != 1]`.

### v0.13.3
- Minor README fix

### v0.13.2
- Fixed PyPI upload

### v0.13.1
- Updated links due to account renaming
- Moved to trusted publishing

### v0.13.0
- Removed check for `json` availability
- Improved README

### v0.12.0
- Added `use_locale_dirs` setting
- Improved file search
- Config reloading is now more consistent

### v0.11.1
- Fixed #25
- (pb) Invalid placeholders will always emit an error

### v0.11.0
- Added `py.typed`
- Added `_list` kwarg to `t` (only for type checkers)
- **(B)** `fallback` is now `None` by default
- (pb) Setting `locale` and `fallback` to the same value will now result in `fallback` being `None`
- Error thrown on missing translation now mentions the locale
- Missing translation is now reported with requested locale instead of fallback one
- Minor optimizations

### v0.10.0
- Simplified static refs pattern
- Added support for braceless placeholders and escaped delimiters
- (pb) If a function registered with `i18n.add_function` raises `KeyError`, it will be reraised instead of being treated as a missing placeholder

### v0.9.1
- Fixed links on PyPI

### v0.9.0
- **(B)** Removed `default=` kwarg of `i18n.t()`. You can work around this change with a custom handler [like this](https://github.com/solaluset/i18nice/blob/01ed6bcd2234998b411f07c92c31639e719dbabb/i18n/tests/translation_tests.py#L147)
- Added docstrings to public API
- Added `__all__` to most files
- Added support for `None` as `fallback`
- (pb) Made memoization enabled by default
- Added `lock=` kwarg to `load_everything()`

### v0.8.1
- Added flake8 and mypy checks
- Enabled and ensured branch coverage
- Added `__all__` to packages
- Added more type hints
- Fixed static references not expanding
- Fixed strict pluralization with translation tuples
- Created `dev-helper.py` for pre-commit and GA
- Made `PythonLoader` throw more verbose error

### v0.8.0
- (pb) `i18n.get("filename_format")` will return `FilenameFormat` instead of string. You can access `template` attribute to get the original string. `set` will continue to work as usual.
- More flexible filename formats
- Type hints for public APIs
- New functions `load_everything` and `unload_everything`
- 100% coverage
- Minor optimizations

### v0.7.0
- Added static references feature
- Added full translation list support

### v0.6.2
- Added PyPI publishing

## Note: versions listed below aren't available on PyPI

### v0.6.0
- (pb) Switched to `yaml.BaseLoader`

### v0.5.1
- Improved memoization (again)

### v0.5.0
- Rewrote `PythonLoader`
- **(B)** Removed old `error_on_missing_*` settings
- Improved memoization
- Improved file loading and fixed bugs
- Improved exceptions
- Added `reload_everything()`
- **(B)** Removed deprecated `other` plural

### v0.4.0
- Trying to set inexistent setting will now raise KeyError
- Added custom functions
- Fixed settings not updating properly
- **(B)** Dropped Python 2
- Added `on_missing_*` hooks

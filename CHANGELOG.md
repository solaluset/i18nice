## Note: **(B)** = BREAKING, (pb) = potentially breaking

### Hint: use `https://github.com/Krutyi-4el/i18nice/compare/v<version 1 (older)>...v<version 2 (newer)>` to see full code difference between versions

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

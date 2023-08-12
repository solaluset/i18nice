class I18nException(Exception):
    """Base class for i18n errors"""

    def __init__(self, value: str):
        self.value = value

    def __str__(self):
        return self.value


class I18nFileLoadError(I18nException):
    """Raised when file load fails"""
    pass


class I18nInvalidStaticRef(I18nException):
    """Raised when static reference cannot be resolved"""
    pass


class I18nInvalidFormat(I18nException):
    """Raised when provided filename_format is invalid"""
    pass

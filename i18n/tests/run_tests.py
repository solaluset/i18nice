import sys
import unittest
from typing import Any, Collection
from os.path import dirname
from importlib.machinery import PathFinder


sys.path.insert(
    0, dirname(dirname(dirname(__file__)))
)


class ModuleDisabler(PathFinder):
    _disabled_modules: Collection[str] = []

    @property
    def disabled_modules(self) -> Collection[str]:
        return self._disabled_modules

    @disabled_modules.setter
    def disabled_modules(self, modules: Collection[str]) -> None:
        for k in modules:
            if k in sys.modules:  # pragma: no branch
                del sys.modules[k]
        self._disabled_modules = modules

    def find_spec(self, name: str, *_: Any) -> None:  # type: ignore[override]
        if name in self.disabled_modules:
            raise ImportError(
                "module {0} is disabled".format(
                    name
                )
            )
        return None


def suite():
    from i18n.tests.loader_tests import (
        TestFileLoader,
    )
    from i18n.tests.translation_tests import (
        TestTranslationFormat,
    )

    suite = unittest.TestSuite()
    loader = unittest.TestLoader()

    suite.addTest(
        loader.loadTestsFromTestCase(
            TestFileLoader
        )
    )
    suite.addTest(
        loader.loadTestsFromTestCase(
            TestTranslationFormat
        )
    )

    return suite


def test_without(modules: Collection[str]) -> None:
    disabler = ModuleDisabler()
    disabler.disabled_modules = modules
    sys.meta_path.insert(0, disabler)
    for k in [
        name
        for name in sys.modules
        if name.startswith("i18n")
    ]:
        del sys.modules[k]
    runner = unittest.TextTestRunner()
    result = runner.run(suite())
    del sys.meta_path[0]
    if not result.wasSuccessful():
        sys.exit(1)  # pragma: no cover


def main():
    test_without(["json"])
    test_without(["yaml"])
    test_without([])


if __name__ == "__main__":
    main()  # pragma: no cover

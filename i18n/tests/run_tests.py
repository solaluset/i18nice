import sys
import unittest
from os.path import dirname

sys.path.insert(0, dirname(dirname(dirname(__file__))))

from i18n.tests.translation_tests import TestTranslationFormat

from i18n.tests.loader_tests import TestFileLoader


def suite():
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()

    suite.addTest(loader.loadTestsFromTestCase(TestFileLoader))
    suite.addTest(loader.loadTestsFromTestCase(TestTranslationFormat))

    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    test_suite = suite()
    result = runner.run(test_suite)
    sys.exit(not result.wasSuccessful())


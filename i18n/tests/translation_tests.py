# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import unittest
import os
import os.path

from i18n import resource_loader
from i18n.translator import t
from i18n import translations
from i18n import config
from i18n import custom_functions

try:
    reload  # Python 2.7
except NameError:
    try:
        from importlib import reload  # Python 3.4+
    except ImportError:
        from imp import reload  # Python 3.0 - 3.3

RESOURCE_FOLDER = os.path.dirname(__file__) + os.sep + 'resources' + os.sep


class TestTranslationFormat(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        resource_loader.init_loaders()
        reload(config)
        config.set('load_path', [os.path.join(RESOURCE_FOLDER, 'translations')])
        translations.add('foo.hi', 'Hello %{name} !')
        translations.add('foo.hi2', 'Hello ${name} !')
        translations.add('foo.hello', 'Salut %{name} !', locale='fr')
        translations.add('foo.basic_plural', {
            'one': '1 elem',
            'many': '%{count} elems'
        })
        translations.add('foo.plural', {
            'zero': 'no mail',
            'one': '1 mail',
            'few': 'only %{count} mails',
            'many': '%{count} mails'
        })
        translations.add('foo.bad_plural', {
            'bar': 'foo elems'
        })
        translations.add('foo.custom_func', '%{count} day%{p(|s)}')
        translations.add('foo.inexistent_func', '%{a(b|c)}')
        translations.add('foo.comma_separated_args', '%{f(1,2,3)}')

    def setUp(self):
        config.set('error_on_missing_translation', False)
        config.set('error_on_missing_placeholder', False)
        config.set('fallback', 'en')
        config.set('locale', 'en')

    def test_basic_translation(self):
        self.assertEqual(t('foo.normal_key'), 'normal_value')

    def test_missing_translation(self):
        self.assertEqual(t('foo.inexistent'), 'foo.inexistent')

    def test_missing_translation_error(self):
        config.set('error_on_missing_translation', True)
        with self.assertRaises(KeyError):
            t('foo.inexistent')

    def test_locale_change(self):
        config.set('locale', 'fr')
        config.set('fallback', 'fr')
        translations.add('foo.goodbye', 'Au revoir!')
        self.assertEqual(t('foo.hello', name='Bob'), 'Salut Bob !')
        self.assertEqual(t('foo.goodbye'), 'Au revoir!')

    def test_fallback(self):
        config.set('fallback', 'fr')
        self.assertEqual(t('foo.hello', name='Bob'), 'Salut Bob !')

    def test_fallback_from_resource(self):
        config.set('fallback', 'ja')
        self.assertEqual(t('foo.fallback_key'), 'フォールバック')

    def test_basic_placeholder(self):
        self.assertEqual(t('foo.hi', name='Bob'), 'Hello Bob !')

    def test_missing_placehoder(self):
        self.assertEqual(t('foo.hi'), 'Hello %{name} !')

    def test_missing_placeholder_error(self):
        config.set('error_on_missing_placeholder', True)
        with self.assertRaises(KeyError):
            t('foo.hi')

    def test_basic_pluralization(self):
        self.assertEqual(t('foo.basic_plural', count=0), '0 elems')
        self.assertEqual(t('foo.basic_plural', count=1), '1 elem')
        self.assertEqual(t('foo.basic_plural', count=2), '2 elems')

    def test_full_pluralization(self):
        self.assertEqual(t('foo.plural', count=0), 'no mail')
        self.assertEqual(t('foo.plural', count=1), '1 mail')
        self.assertEqual(t('foo.plural', count=4), 'only 4 mails')
        self.assertEqual(t('foo.plural', count=12), '12 mails')

    def test_bad_pluralization(self):
        config.set('error_on_missing_plural', False)
        self.assertEqual(t('foo.normal_key', count=5), 'normal_value')
        config.set('error_on_missing_plural', True)
        with self.assertRaises(KeyError):
            t('foo.bad_plural', count=0)

    def test_default(self):
        self.assertEqual(t('inexistent_key', default='foo'), 'foo')

    def test_skip_locale_root_data(self):
        config.set('filename_format', '{locale}.{format}')
        config.set('file_format', 'json')
        config.set('locale', 'gb')
        config.set('skip_locale_root_data', True)
        resource_loader.init_loaders()
        self.assertEqual(t('foo'), 'Lorry')
        config.set('skip_locale_root_data', False)

    def test_skip_locale_root_data_nested_json_dict__default_locale(self):
        config.set("file_format", "json")
        config.set("load_path", [os.path.join(RESOURCE_FOLDER, "translations", "nested_dict_json")])
        config.set("filename_format", "{locale}.{format}")
        config.set('skip_locale_root_data', True)
        config.set("locale", "en")
        resource_loader.init_json_loader()
        self.assertEqual(t('COMMON.START'), 'Start')

    def test_skip_locale_root_data_nested_json_dict__other_locale(self):
        config.set("file_format", "json")
        config.set("load_path", [os.path.join(RESOURCE_FOLDER, "translations", "nested_dict_json")])
        config.set("filename_format", "{locale}.{format}")
        config.set('skip_locale_root_data', True)
        config.set("locale", "en")
        resource_loader.init_json_loader()
        self.assertEqual(t('COMMON.EXECUTE', locale="pl"), 'Wykonaj')

    def test_invalid_setting(self):
        with self.assertRaises(KeyError):
            config.set("asdafs", True)

    def test_custom_function(self):
        config.set('error_on_missing_plural', False)
        custom_functions.add_function('p', lambda **kw: kw['count'] != 1, config.get('locale'))
        self.assertEqual(t('foo.custom_func', count=1), '1 day')
        self.assertEqual(t('foo.custom_func', count=2), '2 days')

    def test_inexistent_function(self):
        config.set('error_on_missing_placeholder', True)
        with self.assertRaises(KeyError):
            t('foo.inexistent_func')

    def test_bad_func(self):
        custom_functions.add_function('p', lambda **kw: kw, config.get('locale'))
        with self.assertRaises(ValueError):
            t('foo.custom_func')

    def test_argument_delimiter_change(self):
        config.set('argument_delimiter', ',')
        custom_functions.add_function('f', lambda **kw: kw['value'] - 1, config.get('locale'))
        self.assertEqual(t('foo.comma_separated_args', value=1), '1')
        config.set('argument_delimiter', '|')

    def test_placeholder_delimiter_change(self):
        config.set('placeholder_delimiter', '$')
        self.assertEqual(t('foo.hi2', name='Bob'), 'Hello Bob !')

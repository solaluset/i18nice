# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import unittest
import os
import os.path
from importlib import reload

from i18n import resource_loader
from i18n.translator import t
from i18n import translations
from i18n import config
from i18n import custom_functions
from i18n import formatters


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
            'bar': 'foo elems',
            'baz': 'bar elems'
        })
        translations.add('foo.custom_func', '%{count} day%{p(|s)}')
        translations.add('foo.inexistent_func', '%{a(b|c)}')
        translations.add('foo.comma_separated_args', '%{f(1,2,3)}')
        translations.add(
            "foo.no_args_func",
            "%count1 apples, %count2 bananas, %total() fruits total",
        )

        custom_functions.add_function('p', lambda *a, **kw: a[kw['count'] != 1])

    def setUp(self):
        config.set('on_missing_translation', None)
        config.set('on_missing_placeholder', None)
        config.set('on_missing_plural', None)
        config.set('fallback', 'en')
        config.set('locale', 'en')
        config.set('file_format', 'py')
        custom_functions.locales_functions.clear()

    def test_basic_translation(self):
        self.assertEqual(t('foo.normal_key'), 'normal_value')

    def test_missing_translation(self):
        self.assertEqual(t('foo.inexistent'), 'foo.inexistent')

    def test_missing_translation_error(self):
        config.set('on_missing_translation', 'error')
        with self.assertRaises(KeyError):
            t('foo.inexistent')

    def test_missing_translation_handler(self):
        def handler(key, locale):
            return key + '_' + locale

        config.set("fallback", "fr")
        config.set('on_missing_translation', handler)
        self.assertEqual(t('foo.inexistent'), 'foo.inexistent_en')

    def test_locale_change(self):
        config.set('locale', 'fr')
        config.set('fallback', 'fr')
        translations.add('foo.goodbye', 'Au revoir!')
        self.assertEqual(t('foo.hello', name='Bob'), 'Salut Bob !')
        self.assertEqual(t('foo.goodbye'), 'Au revoir!')

    def test_fallback(self):
        config.set('fallback', 'fr')
        self.assertEqual(t('foo.hello', name='Bob'), 'Salut Bob !')
        config.set("fallback", None)
        self.assertEqual(t("foo.hello"), "foo.hello")

    def test_fallback_from_resource(self):
        config.set('fallback', 'ja')
        self.assertEqual(t('foo.fallback_key'), 'フォールバック')

    def test_clear_one_locale(self):
        config.set("locale", "testloc")
        config.set("fallback", "en")
        translations.add("test", "123")
        translations.add("test", "321", config.get("fallback"))
        self.assertEqual(t("test"), "123")
        translations.clear("testloc")
        # also try something inexistent
        translations.clear("testloc-abc")
        self.assertEqual(t("test"), "321")

    def test_basic_placeholder(self):
        self.assertEqual(t('foo.hi', name='Bob'), 'Hello Bob !')

    def test_braceless_placeholder(self):
        translations.add("a", "%p(Hello|Goodbye) %name!")
        self.assertEqual(t("a", name="test", count=1), "Hello test!")

    def test_delimiter_escape(self):
        # throw an error if escape is not recognised
        config.set("on_missing_placeholder", "error")
        translations.add("p", "%percent%%")
        formatters.expand_static_refs(("p",), config.get("locale"))
        self.assertEqual(t("p", percent=99), "99%")

    def test_missing_placehoder(self):
        self.assertEqual(t('foo.hi'), 'Hello %{name} !')

    def test_missing_placeholder_error(self):
        config.set('on_missing_placeholder', 'error')
        with self.assertRaises(KeyError):
            t('foo.hi')

    def test_missing_placeholder_handler(self):
        def handler(translation_key, locale, text, key):
            if key == "name":  # pragma: no branch
                return 'stranger'

        config.set('on_missing_placeholder', handler)
        self.assertEqual(t('foo.hi'), 'Hello stranger !')

    def test_invalid_placeholder(self):
        translations.add("p", "invalid: %")
        with self.assertRaises(ValueError):
            t("p")

    def test_placeholder_named_key(self):
        translations.add("a", "%{key}")
        self.assertEqual(t("a", key="b"), "b")

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
        config.set('on_missing_plural', 'error')
        with self.assertRaises(KeyError):
            t('foo.bad_plural', count=0)

    def test_bad_pluralization_handler(self):
        def handler(key, locale, translation, count):
            if isinstance(translation, dict):
                return translation[sorted(translation.keys())[count]]
            return key  # pragma: no cover

        config.set('on_missing_plural', handler)
        self.assertEqual(t('foo.bad_plural', count=0), 'foo elems')
        self.assertEqual(t('foo.bad_plural', count=1), 'bar elems')

    def test_default(self):
        def return_default(key, locale, **kwargs):
            return kwargs.pop("default", key)
        config.set("on_missing_translation", return_default)
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
        self.assertEqual(t('foo.custom_func', count=1), '1 day')
        self.assertEqual(t('foo.custom_func', count=2), '2 days')

    def test_inexistent_function(self):
        config.set('on_missing_placeholder', "error")
        with self.assertRaises(KeyError):
            t('foo.inexistent_func')

    def test_function_without_args(self):
        custom_functions.add_function(
            "total",
            lambda **kw: kw["count1"] + kw["count2"],
            config.get("locale"),
        )
        self.assertEqual(
            t("foo.no_args_func", count1=7, count2=3),
            "7 apples, 3 bananas, 10 fruits total",
        )

    def test_bad_locale_func(self):
        custom_functions.add_function(
            "p",
            lambda *a, **kw: a[kw["lol"]],
            config.get("locale"),
        )
        with self.assertRaises(KeyError):
            t('foo.custom_func')

    def test_argument_delimiter_change(self):
        config.set('argument_delimiter', ',')
        custom_functions.add_function(
            "f",
            lambda *a, **kw: a[kw["value"] - 1],
            config.get("locale"),
        )
        try:
            self.assertEqual(t("foo.comma_separated_args", value=1), "1")
        finally:
            config.set("argument_delimiter", "|")

    def test_placeholder_delimiter_change(self):
        config.set('placeholder_delimiter', '$')
        self.assertEqual(t('foo.hi2', name='Bob'), 'Hello Bob !')
        # should revert changes back
        self.setUpClass()
        self.assertNotEqual(t('foo.hi2', name='Bob'), 'Hello Bob !')

    def test_path_with_hyphen(self):
        config.set("file_format", "json")
        config.set("filename_format", "{namespace}.{format}")
        self.assertEqual(t("with-hyphen.test"), "ok")

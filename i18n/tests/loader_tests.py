# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import unittest
from unittest import mock
import os
import os.path
import tempfile
from importlib import reload

import i18n
from i18n import resource_loader
from i18n.errors import I18nFileLoadError, I18nInvalidFormat
from i18n.translator import t
from i18n import config
from i18n.config import json_available, yaml_available
from i18n import translations, formatters
from i18n.loaders import Loader


RESOURCE_FOLDER = os.path.join(os.path.dirname(__file__), "resources")


class TestFileLoader(unittest.TestCase):
    def setUp(self):
        resource_loader.loaders = {}
        translations.container = {}
        reload(config)
        config.set("load_path", [os.path.join(RESOURCE_FOLDER, "translations")])
        config.set("filename_format", "{namespace}.{locale}.{format}")
        config.set("encoding", "utf-8")

    def test_load_unavailable_extension(self):
        with self.assertRaisesRegex(I18nFileLoadError, "no loader .*"):
            resource_loader.load_resource("foo.bar", "baz")

    def test_register_wrong_loader(self):
        class WrongLoader(object):
            pass
        class BadLoader(Loader):
            pass
        with self.assertRaises(ValueError):
            resource_loader.register_loader(WrongLoader, [])
        with self.assertRaises(NotImplementedError):
            BadLoader().load_resource(
                os.path.join(RESOURCE_FOLDER, "translations", "en.json"),
                None,
                False,
            )

    def test_loader_for_two_exts_is_same_obj(self):
        resource_loader.register_loader(Loader, ["x", "y"])
        self.assertIs(resource_loader.loaders["x"], resource_loader.loaders["y"])

    def test_register_python_loader(self):
        resource_loader.init_python_loader()
        with self.assertRaisesRegex(I18nFileLoadError, "error loading file .*"):
            resource_loader.load_resource("foo.py", "bar")

    @unittest.skipUnless(yaml_available, "yaml library not available")
    def test_register_yaml_loader(self):
        resource_loader.init_yaml_loader()
        with self.assertRaisesRegex(I18nFileLoadError, "error loading file .*"):
            resource_loader.load_resource("foo.yml", "bar")

    @unittest.skipUnless(json_available, "json library not available")
    def test_load_wrong_json_file(self):
        resource_loader.init_json_loader()
        with self.assertRaisesRegex(I18nFileLoadError, "error getting data .*"):
            resource_loader.load_resource(os.path.join(RESOURCE_FOLDER, "settings", "dummy_config.json"), "foo")
        with self.assertRaisesRegex(I18nFileLoadError, "invalid JSON: .*"):
            resource_loader.load_resource(os.path.join(RESOURCE_FOLDER, "translations", "invalid.json"), "foo")

    @unittest.skipUnless(yaml_available, "yaml library not available")
    def test_load_yaml_file(self):
        resource_loader.init_yaml_loader()
        data = resource_loader.load_resource(os.path.join(RESOURCE_FOLDER, "settings", "dummy_config.yml"), "settings")
        self.assertIn("foo", data)
        self.assertEqual("bar", data["foo"])

    @unittest.skipUnless(yaml_available, "yaml library not available")
    def test_override_yaml_loader(self):
        import yaml

        class MyLoader(i18n.loaders.YamlLoader):
            loader = yaml.FullLoader

        file = os.path.join(RESOURCE_FOLDER, "settings", "dummy_config.yml")

        resource_loader.init_yaml_loader()
        data = resource_loader.load_resource(file, "settings")
        self.assertIsInstance(data["maybe_bool"], str)

        i18n.register_loader(MyLoader, ["yml", "yaml"])
        data = resource_loader.load_resource(file, "settings")
        self.assertIsInstance(data["maybe_bool"], bool)

    @unittest.skipUnless(yaml_available, "yaml library not available")
    def test_load_broken_yaml(self):
        resource_loader.init_yaml_loader()
        with self.assertRaisesRegex(I18nFileLoadError, "invalid YAML: .*"):
            resource_loader.load_resource(os.path.join(RESOURCE_FOLDER, "translations", "invalid.yml"), "foo")

    @unittest.skipUnless(json_available, "json library not available")
    def test_load_json_file(self):
        resource_loader.init_json_loader()
        data = resource_loader.load_resource(os.path.join(RESOURCE_FOLDER, "settings", "dummy_config.json"), "settings")
        self.assertIn("foo", data)
        self.assertEqual("bar", data["foo"])

    def test_load_python_file(self):
        resource_loader.init_python_loader()
        data = resource_loader.load_resource(os.path.join(RESOURCE_FOLDER, "settings", "dummy_config.py"), "settings")
        self.assertIn("foo", data)
        self.assertEqual("bar", data["foo"])

    def test_memoization_with_file(self):
        """This test creates two files.
        First is a dummy file.
        Second is a script that will remove the dummy file and load a dict of translations.
        Then we try to translate inexistent key to ensure that the script is not executed again.
        """
        config.set("enable_memoization", True)
        config.set("file_format", "py")
        resource_loader.init_python_loader()
        memoization_file_name = 'memoize.en.py'
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            i18n.load_path.append(tmp_dir_name)
            dummy = os.path.join(tmp_dir_name, "dummy.txt")
            open(dummy, "w").close()
            fd = open(os.path.join(tmp_dir_name, memoization_file_name), 'w')
            fd.write(f'''
import os

os.remove({dummy!r})

en = {{"key": "value"}}
            ''')
            fd.close()
            self.assertEqual(t('memoize.key'), 'value')
            # change relative path to test if file path is stored properly
            orig_wd = os.getcwd()
            os.chdir(tmp_dir_name)
            i18n.load_path[0] = "."
            try:
                self.assertEqual(t('memoize.key2'), 'memoize.key2')
            finally:
                os.chdir(orig_wd)

    @unittest.skipUnless(json_available, "json library not available")
    def test_load_everything(self):
        i18n.load_path[0] = os.path.join(RESOURCE_FOLDER, "translations", "bar")
        config.set("file_format", "json")
        resource_loader.init_json_loader()

        i18n.load_everything()
        self.assertTrue(translations.has("a.abc.x", "en"))
        i18n.unload_everything()
        self.assertFalse(translations.has("a.abc.x", "en"))
        i18n.load_everything("en")
        self.assertTrue(translations.has("a.abc.x", "en"))
        i18n.unload_everything()
        config.set("filename_format", "{namespace}.{format}")
        i18n.load_everything()
        self.assertTrue(translations.has("d.d", "en"))
        i18n.unload_everything()
        config.set("skip_locale_root_data", True)
        i18n.load_everything("en")
        self.assertTrue(translations.has("d.en.d", "en"))
        i18n.unload_everything()
        with self.assertRaises(I18nFileLoadError):
            i18n.load_everything()

    @unittest.skipUnless(json_available, "json library not available")
    def test_reload_everything(self):
        config.set("skip_locale_root_data", True)
        config.set("file_format", "json")
        resource_loader.init_json_loader()
        with tempfile.TemporaryDirectory() as tmp_dir:
            i18n.load_path.append(tmp_dir)
            filename = os.path.join(tmp_dir, "test.en.json")
            with open(filename, "w") as f:
                f.write('{"a": "b"}')
            self.assertEqual(t("test.a"), "b")
            i18n.unload_everything()
            self.assertEqual(translations.container, {})

            # rewrite file and reload
            with open(filename, "w") as f:
                f.write('{"a": "c"}')
            i18n.reload_everything()
            self.assertEqual(t("test.a"), "c")

    def test_multilingual_caching(self):
        resource_loader.init_python_loader()
        config.set("enable_memoization", True)
        config.set("filename_format", "{namespace}.{format}")
        config.set("file_format", "py")
        self.assertEqual(t("multilingual.hi"), "Hello")
        self.assertEqual(t("multilingual.hi", locale="uk"), "Привіт")

    @unittest.skipUnless(json_available, "json library not available")
    def test_load_file_with_strange_encoding(self):
        resource_loader.init_json_loader()
        config.set("encoding", "euc-jp")
        data = resource_loader.load_resource(os.path.join(RESOURCE_FOLDER, "settings", "eucjp_config.json"), "settings")
        self.assertIn("ほげ", data)
        self.assertEqual("ホゲ", data["ほげ"])

    def test_get_namespace_from_filepath_with_filename(self):
        tests = {
            "foo": "foo.ja.yml",
            "foo.bar": os.path.join("foo", "bar.ja.yml"),
            "foo.bar.baz": os.path.join("foo", "bar", "baz.en.yml"),
        }
        for expected, test_val in tests.items():
            namespace = resource_loader.get_namespace_from_filepath(test_val)
            self.assertEqual(expected, namespace)

    def test_get_namespace_from_filepath_without_filename(self):
        tests = {
            "": "ja.yml",
            "foo": os.path.join("foo", "ja.yml"),
            "foo.bar": os.path.join("foo", "bar", "en.yml"),
        }
        config.set("filename_format", "{locale}.{format}")
        for expected, test_val in tests.items():
            namespace = resource_loader.get_namespace_from_filepath(test_val)
            self.assertEqual(expected, namespace)

    def test_get_namespace_from_filepath_strange_format(self):
        config.set("filename_format", "{locale}.{namespace}.{format}")
        namespace = resource_loader.get_namespace_from_filepath("x.y.z")
        self.assertEqual(namespace, "y")
        config.set("filename_format", "{namespace}-{locale}.{format}")
        namespace = resource_loader.get_namespace_from_filepath("x-y.z")
        self.assertEqual(namespace, "x")

    def test_invalid_filename_format(self):
        with self.assertRaises(AttributeError):
            config.get("filename_format").has_something
        with self.assertRaisesRegex(I18nInvalidFormat, "Can't apply .+"):
            config.set("filename_format", "{format!r}")
        with self.assertRaisesRegex(I18nInvalidFormat, "Unknown placeholder .+ 'formatus'"):
            config.set("filename_format", "{formatus}")

    def test_formatters_misc(self):
        with self.assertRaises(NotImplementedError):
            formatters.Formatter("", "", "", {}).format()

        self.assertEqual(repr(formatters.FilenameFormat("", {})), "FilenameFormat('', {})")

    @unittest.skipUnless(yaml_available, "yaml library not available")
    def test_load_translation_file(self):
        resource_loader.init_yaml_loader()
        resource_loader.load_translation_file("foo.en.yml", os.path.join(RESOURCE_FOLDER, "translations"))

        self.assertTrue(translations.has("foo.normal_key"))
        self.assertTrue(translations.has("foo.parent.nested_key"))
        self.assertIsInstance(translations.get("foo.welcome"), tuple)

    @unittest.skipUnless(yaml_available, "yaml library not available")
    def test_translation_list(self):
        resource_loader.init_yaml_loader()
        resource_loader.load_translation_file("foo.en.yml", os.path.join(RESOURCE_FOLDER, "translations"))

        default_format = formatters.TranslationFormatter.format
        call_count = 0

        def patched_format(obj):
            nonlocal call_count

            call_count += 1
            return default_format(obj)

        with mock.patch(
            "i18n.formatters.TranslationFormatter.format",
            side_effect=patched_format,
            autospec=True
        ):
            self.assertEqual(t("foo.welcome", name="John")[0], "Hi John")
            self.assertEqual(t("foo.welcome", name="Sam", count=2)[1], "Hello Sam and friends")
            # 1 call + 2 recursive
            self.assertEqual(t("foo.welcome", name="Sam", count=1)[:2], ("Hi Sam", "Hello Sam"))
        self.assertEqual(call_count, 5)

    @unittest.skipUnless(yaml_available, "yaml library not available")
    def test_load_plural(self):
        resource_loader.init_yaml_loader()
        resource_loader.load_translation_file("foo.en.yml", os.path.join(RESOURCE_FOLDER, "translations"))
        self.assertTrue(translations.has("foo.mail_number"))
        translated_plural = translations.get("foo.mail_number")
        self.assertIsInstance(translated_plural, dict)
        self.assertEqual(translated_plural["zero"], "You do not have any mail.")
        self.assertEqual(translated_plural["one"], "You have a new mail.")
        self.assertEqual(translated_plural["many"], "You have %{count} new mails.")

    @unittest.skipUnless(yaml_available, "yaml library not available")
    def test_search_translation_yaml(self):
        resource_loader.init_yaml_loader()
        config.set("file_format", "yml")
        resource_loader.search_translation("foo.normal_key")
        self.assertTrue(translations.has("foo.normal_key"))

    @unittest.skipUnless(json_available, "json library not available")
    def test_search_translation_json(self):
        resource_loader.init_json_loader()
        config.set("file_format", "json")

        resource_loader.search_translation("bar.baz.qux")
        self.assertTrue(translations.has("bar.baz.qux"))

    @unittest.skipUnless(json_available, "json library not available")
    def test_search_translation_without_ns(self):
        resource_loader.init_json_loader()
        config.set("file_format", "json")
        config.set("filename_format", "{locale}.{format}")
        resource_loader.search_translation("foo")
        self.assertTrue(translations.has("foo"))

    @unittest.skipUnless(json_available, "json library not available")
    def test_search_translation_path_as_ns(self):
        resource_loader.init_json_loader()
        config.set("file_format", "json")
        config.set("load_path", [RESOURCE_FOLDER])
        config.set("filename_format", "{locale}.{format}")
        resource_loader.search_translation("translations.foo")
        self.assertTrue(translations.has("translations.foo"))

    @unittest.skipUnless(json_available, "json library not available")
    def test_search_translation_without_ns_nested_dict__two_levels_neting__default_locale(self):
        resource_loader.init_json_loader()
        config.set("file_format", "json")
        config.set("load_path", [os.path.join(RESOURCE_FOLDER, "translations", "nested_dict_json")])
        config.set("filename_format", "{locale}.{format}")
        config.set('skip_locale_root_data', True)
        config.set("locale", "en")
        resource_loader.search_translation("COMMON.VERSION")
        self.assertTrue(translations.has("COMMON.VERSION"))
        self.assertEqual(translations.get("COMMON.VERSION"), "version")

    @unittest.skipUnless(json_available, "json library not available")
    def test_search_translation_without_ns_nested_dict__two_levels_neting__other_locale(self):
        resource_loader.init_json_loader()
        config.set("file_format", "json")
        config.set("load_path", [os.path.join(RESOURCE_FOLDER, "translations", "nested_dict_json")])
        config.set("filename_format", "{locale}.{format}")
        config.set('skip_locale_root_data', True)
        config.set("locale", "en")
        resource_loader.search_translation("COMMON.VERSION", locale="pl")
        self.assertTrue(translations.has("COMMON.VERSION", locale="pl"))
        self.assertEqual(translations.get("COMMON.VERSION", locale="pl"), "wersja")

    @unittest.skipUnless(json_available, "json library not available")
    def test_search_translation_without_ns_nested_dict__default_locale(self):
        resource_loader.init_json_loader()
        config.set("file_format", "json")
        config.set("load_path", [os.path.join(RESOURCE_FOLDER, "translations", "nested_dict_json")])
        config.set("filename_format", "{locale}.{format}")
        config.set('skip_locale_root_data', True)
        config.set("locale", "en")
        resource_loader.search_translation("TOP_MENU.TOP_BAR.LOGS")
        self.assertTrue(translations.has("TOP_MENU.TOP_BAR.LOGS"))
        self.assertEqual(translations.get("TOP_MENU.TOP_BAR.LOGS"), "Logs")

    @unittest.skipUnless(json_available, "json library not available")
    def test_search_translation_without_ns_nested_dict__other_locale(self):
        resource_loader.init_json_loader()
        config.set("file_format", "json")
        config.set("load_path", [os.path.join(RESOURCE_FOLDER, "translations", "nested_dict_json")])
        config.set("filename_format", "{locale}.{format}")
        config.set('skip_locale_root_data', True)
        config.set("locale", "en")
        resource_loader.search_translation("TOP_MENU.TOP_BAR.LOGS", locale="pl")
        self.assertTrue(translations.has("TOP_MENU.TOP_BAR.LOGS", locale="pl"))
        self.assertEqual(translations.get("TOP_MENU.TOP_BAR.LOGS", locale="pl"), "Logi")

    def test_load_config(self):
        resource_loader.init_python_loader()
        resource_loader.load_config(os.path.join(RESOURCE_FOLDER, "settings", "working_config.py"))
        self.assertEqual(config.get("locale"), "test")
        self.assertEqual(config.get("fallback"), "en")

    def test_set_load_path(self):
        self.assertIs(i18n.load_path, config.get("load_path"))
        config.set("load_path", [])
        self.assertIs(i18n.load_path, config.get("load_path"))
        reload(config)
        self.assertIs(i18n.load_path, config.get("load_path"))


    @unittest.skipUnless(json_available, "json library not available")
    def test_static_references(self):
        resource_loader.init_json_loader()
        config.set("file_format", "json")
        config.set("load_path", [os.path.join(RESOURCE_FOLDER, "translations")])
        config.set("filename_format", "{namespace}.{format}")
        config.set('skip_locale_root_data', True)
        config.set("locale", "en")

        self.assertEqual(t("static_ref.welcome"), "Welcome to Programname")
        self.assertEqual(t("static_ref.cool.best"), "Programname is the best program ever!")
        self.assertEqual(t("static_ref.cool.downloads", count=0), "Programname was never downloaded :(")
        self.assertEqual(t("static_ref.cool.downloads", count=10), "Programname was downloaded 10 times!")
        self.assertEqual(t("static_ref.otherFile"), "FooBar")

        i18n.add_function("f", lambda: 0)
        self.assertEqual(t("static_ref.asArgument"), "ver")

        with self.assertRaises(RecursionError):
            t("static_ref2.foo")

        config.set("namespace_delimiter", "/")
        with self.assertRaises(i18n.I18nInvalidStaticRef):
            t("static_ref2/x")

    def test_static_ref_expansion(self):
        locale = config.get("locale")
        i18n.add_translation("a.b", "%{.c}")
        i18n.add_translation("a.c", "c")
        i18n.add_translation("b", "%{.a.b}")

        formatters.expand_static_refs(("b",), locale)
        self.assertEqual(translations.get("b"), "c")

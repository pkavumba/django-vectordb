import os

import pytest
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from vectordb.settings import VectorDBSettings, import_from_string, perform_import

# Test data
TEST_DEFAULTS = {
    "TEST_SETTING_1": "test_value_1",
    "TEST_SETTING_2": "vectordb.tests.dummy_module.TEST_SETTING_2",
}

TEST_IMPORT_STRINGS = ["TEST_SETTING_2"]

TEST_REMOVED_SETTINGS = ["TEST_SETTING_3"]

TEST_USER_SETTINGS = {
    "TEST_SETTING_1": "user_test_value_1",
    "TEST_SETTING_2": "vectordb.tests.dummy_module.USER_TEST_SETTING_2",
    "TEST_SETTING_3": "user_test_value_3",
}


def test_import_from_string():
    assert import_from_string("os.path.join", "TEST_SETTING_1") == os.path.join
    with pytest.raises(ImportError):
        import_from_string("invalid.module.path", "TEST_SETTING_1")


def test_perform_import():
    assert perform_import(None, "TEST_SETTING_1") is None
    assert perform_import("os.path.join", "TEST_SETTING_1") == os.path.join
    assert perform_import(["os.path", "os.path.join"], "TEST_SETTING_1") == [
        os.path,
        os.path.join,
    ]
    assert perform_import(42, "TEST_SETTING_1") == 42

    with pytest.raises(ImportError):
        perform_import("invalid.module.path", "TEST_SETTING_1")


def test_vectordb_settings_default_values():
    settings = VectorDBSettings(None, TEST_DEFAULTS, TEST_IMPORT_STRINGS)
    assert settings.TEST_SETTING_1 == "test_value_1"
    assert settings.TEST_SETTING_2 == "test_value_2"


def test_vectordb_settings_user_values():
    settings = VectorDBSettings(TEST_USER_SETTINGS, TEST_DEFAULTS, TEST_IMPORT_STRINGS)
    assert settings.TEST_SETTING_1 == "user_test_value_1"
    assert settings.TEST_SETTING_2 == "user_test_value_2"


def test_vectordb_settings_invalid_attribute():
    settings = VectorDBSettings(None, TEST_DEFAULTS, TEST_IMPORT_STRINGS)
    with pytest.raises(AttributeError):
        settings.NON_EXISTENT_SETTING


def test_vectordb_settings_reload():
    settings = VectorDBSettings(TEST_USER_SETTINGS, TEST_DEFAULTS, TEST_IMPORT_STRINGS)
    with override_settings(
        DJANGO_VECTOR_DB={"TEST_SETTING_1": "new_user_test_value_1"}
    ):
        settings.reload()
        assert settings.TEST_SETTING_1 == "new_user_test_value_1"


def test_vectordb_settings_reload_without_user_settings():
    settings = VectorDBSettings(None, TEST_DEFAULTS, TEST_IMPORT_STRINGS)
    with override_settings(
        DJANGO_VECTOR_DB={"TEST_SETTING_1": "new_user_test_value_1"}
    ):
        settings.reload()
        assert settings.TEST_SETTING_1 == "new_user_test_value_1"

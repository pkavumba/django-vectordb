from __future__ import annotations

# Inspired by rest framework
import os

from django.conf import settings
from django.core.signals import setting_changed
from django.utils.module_loading import import_string

DEFAULTS = {
    "DEFAULT_EMBEDDING_CLASS": "vectordb.embedding_functions.SentenceTransformerEncoder",
    "DEFAULT_EMBEDDING_MODEL": "all-MiniLM-L6-v2",
    "DEFAULT_EMBEDDING_SPACE": "l2",
    "DEFAULT_EMBEDDING_DIMENSION": 384,
    "DEFAULT_MAX_N_RESULTS": 10,
    "DEFAULT_MIN_SCORE": 0.0,
    "DEFAULT_MAX_BRUTEFORCE_N": 10_000,
    "DEFAULT_PERSISTENT_DIRECTORY": os.path.join(settings.BASE_DIR, ".vectordb"),
}


IMPORT_STRINGS = [
    "DEFAULT_EMBEDDING_CLASS",
]


REMOVED_SETTINGS = []


def perform_import(val, setting_name):
    if val is None:
        return None
    elif isinstance(val, str):
        return import_from_string(val, setting_name)
    elif isinstance(val, (list, tuple)):
        return [import_from_string(item, setting_name) for item in val]
    return val


def import_from_string(val, setting_name):
    try:
        return import_string(val)
    except ImportError as e:
        msg = "Could not import '%s' for setting '%s'. %s: %s." % (
            val,
            setting_name,
            e.__class__.__name__,
            e,
        )
        raise ImportError(msg)


class VectorDBSettings:
    """
    A settings object that allows vectordb settings to be accessed as
    properties. For example:

        from vectordb.settings import vectordb_settings
        print(vectordb_settings.DEFAULT_EMBEDDING_CLASS)

    Any setting with string import paths will be automatically resolved
    and return the class, rather than the string literal.
    """

    def __init__(self, user_settings=None, defaults=None, import_strings=None):
        if user_settings:
            self._user_settings = self.__check_user_settings(user_settings)
        self.defaults = defaults or DEFAULTS
        self.import_strings = import_strings or IMPORT_STRINGS
        self._cached_attrs = set()

    @property
    def user_settings(self):
        if not hasattr(self, "_user_settings"):
            self._user_settings = getattr(settings, "DJANGO_VECTOR_DB", {})
        return self._user_settings

    def __getattr__(self, attr):
        if attr not in self.defaults:
            raise AttributeError("Invalid DJANGO_VECTOR_DB setting: '%s'" % attr)

        try:
            # Check if present in user settings
            val = self.user_settings[attr]
        except KeyError:
            # use defaults
            val = self.defaults[attr]

        if attr in self.import_strings:
            val = perform_import(val, attr)

        # Cache the result
        self._cached_attrs.add(attr)
        setattr(self, attr, val)
        return val

    def __check_user_settings(self, user_settings):
        for setting in REMOVED_SETTINGS:
            if setting in user_settings:
                raise RuntimeError(
                    "The '%s' setting has been removed. Please refer to '%s' for available settings."  # noqa E501
                    % (setting, "https://github.com/pkavumba/django-vectordb")
                )
        return user_settings

    def reload(self):
        for attr in self._cached_attrs:
            delattr(self, attr)
        self._cached_attrs.clear()
        if hasattr(self, "_user_settings"):
            delattr(self, "_user_settings")


vectordb_settings = VectorDBSettings(None, DEFAULTS, IMPORT_STRINGS)


def reload_vectordb_settings(*args, **kwargs):
    setting = kwargs["setting"]
    if setting == "DJANGO_VECTOR_DB":
        vectordb_settings.reload()


setting_changed.connect(reload_vectordb_settings)

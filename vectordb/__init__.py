from __future__ import annotations

from django.apps import apps as django_apps


def get_vectordb_model():
    return django_apps.get_model("vectordb", "Vector")


class VectorProxy:
    def __getattr__(self, name):
        Vector = get_vectordb_model()
        return getattr(Vector.objects, name)


vectordb = VectorProxy()

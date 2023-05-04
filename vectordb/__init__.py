from django.apps import apps


def get_vectordb_model():
    return apps.get_model("vectordb", "Vector")


class VectorProxy:
    def __getattr__(self, name):
        Vector = apps.get_model("vectordb", "Vector")
        return getattr(Vector.objects, name)


vectordb = VectorProxy()

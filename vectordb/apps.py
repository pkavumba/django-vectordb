from django.apps import AppConfig


class VectordbConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "vectordb"

    def ready(self) -> None:
        from .signals import delete_vector_index, update_vector_index  # noqa

from django.apps import AppConfig


class VectordbConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "vectordb"

    def ready(self) -> None:
        from .signals import update_vector_index, delete_vector_index

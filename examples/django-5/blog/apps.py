from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "blog"

    def ready(self):
        from vectordb.shortcuts import autosync_model_to_vectordb

        from .models import Post

        autosync_model_to_vectordb(Post)

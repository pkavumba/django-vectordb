from __future__ import annotations

from django.db.models.signals import post_delete, post_save

from .sync_signals import sync_vectordb_on_create_update, sync_vectordb_on_delete

# Define a global set to store the registered model classes
registered_models = set()


def autosync_model_to_vectordb(model_class):
    # Get the app label and the model name of the model class
    app_label = model_class._meta.app_label
    model_name = model_class.__name__
    # Form a unique key for the model class
    model_key = f"vectordb.{app_label}.{model_name}"

    # Check if the model class is already registered
    if model_key not in registered_models:
        # Connect the handler functions to the signals for the model class
        #  with the model key as the dispatch uid
        post_save.connect(
            sync_vectordb_on_create_update, sender=model_class, dispatch_uid=model_key
        )
        post_delete.connect(
            sync_vectordb_on_delete, sender=model_class, dispatch_uid=model_key
        )
        # Add the model key to the set of registered models
        registered_models.add(model_key)

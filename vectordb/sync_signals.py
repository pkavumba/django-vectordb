from __future__ import annotations

import logging

import numpy as np
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Vector


def sync_vectordb_on_create_update(sender, instance, created, **kwargs):
    """
    Signal to save or update the vectordb when an instance is created or updated.
    """
    content_type = ContentType.objects.get_for_model(instance)
    if (
        created
        or not Vector.objects.filter(
            content_type=content_type, object_id=instance.pk
        ).exists()
    ):
        # Create a new entry in the Vector model
        vector = Vector.objects.add_instance(instance)
    else:
        # Save the instance to the Vector database if it doesn't exist, else update it
        vector = Vector.objects.get(content_type=content_type, object_id=instance.pk)

        # Extract the text using the get_vectordb_text method
        text = instance.get_vectordb_text()
        metadata = instance.get_vectordb_metadata()
        vector.metadata = metadata

        if text == vector.text:
            # If the text is the same, don't update the vector
            vector.save()  # save the metadata anyway
            return
        else:
            # Else, update the vector
            vector.text = text

            # Convert the text to embeddings using the Manager's embedding_fn
            vector.embedding = (
                Vector.objects.embedding_fn(text).astype("float32").tobytes()
            )
            vector.save()


def sync_vectordb_on_delete(sender, instance, **kwargs):
    """
    Signal to delete an entry from the vectordb when an instance is deleted.
    """
    # Delete the instance from the Vector model
    content_type = ContentType.objects.get_for_model(instance)
    vector = Vector.objects.filter(content_type=content_type, object_id=instance.pk)
    vector.delete()

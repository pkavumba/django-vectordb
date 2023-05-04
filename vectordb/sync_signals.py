from __future__ import annotations

import logging
import numpy as np
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType

from .models import Vector


def sync_vectordb_on_create_update(sender, instance, created, **kwargs):
    """
    Signal to save or update the vectordb when an instance is created or updated.
    """
    # Extract the text using the get_text method
    text = instance.get_text()

    # Convert the text to embeddings using the Manager's embedding_fn
    embedding = Vector.objects.embedding_fn(text)

    # Save the instance to the Vector database if it doesn't exist, else update it
    content_type = ContentType.objects.get_for_model(instance)
    vector, _ = Vector.objects.get_or_create(
        content_type=content_type, object_id=instance.pk
    )
    vector.embedding = embedding.tobytes()
    vector.text = text
    vector.save()


def sync_vectordb_on_delete(sender, instance, **kwargs):
    """
    Signal to delete an entry from the vectordb when an instance is deleted.
    """
    # Delete the instance from the Vector model
    content_type = ContentType.objects.get_for_model(instance)
    vector = Vector.objects.filter(content_type=content_type, object_id=instance.pk)
    vector.delete()

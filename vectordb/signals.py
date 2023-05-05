from __future__ import annotations

import logging
import numpy as np
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType

from .models import Vector


# Get an instance of a logger
logger = logging.getLogger("VectorDB")
logger.setLevel(logging.DEBUG)


@receiver(post_save, sender=Vector, dispatch_uid="update_vector_index_unique_id")
def update_vector_index(sender, instance, created, **kwargs):
    """
    Signal to update the HNSWIndex when a Vector instance is updated.
    """
    # Ensure VectorManager has an instance of HNSWIndex
    if sender.objects.index is not None:
        embedding = instance.vector
        id = instance.id

        # If instance is created, add it to the index
        if created:
            sender.objects.index.add(embedding, np.array([id]))
        # If instance is updated, update the index with the new embedding
        else:
            sender.objects.index.update(embedding, np.array([id]))


@receiver(post_delete, sender=Vector, dispatch_uid="delete_vector_index_unique_id")
def delete_vector_index(sender, instance, **kwargs):
    """
    Signal to delete the index when a Vector instance is deleted.
    """
    # Ensure VectorManager has an instance of HNSWIndex
    if sender.objects.index is not None:
        # Get the id from the deleted instance
        id = instance.id

        # Delete the index with the given id
        sender.objects.index.delete(np.array([id]))

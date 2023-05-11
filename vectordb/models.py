from __future__ import annotations

import numpy as np
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models

from .manager import VectorManager


def validate_embedding(value):
    """
    Custom validator to ensure that the embedding is not empty or null.
    """
    if value is None or len(value) == 0:
        raise ValidationError("Embedding must be set and not be an empty bytes.")


class Vector(models.Model):
    """A vector db model that can be used to store embeddings for any Django model."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    embedding = models.BinaryField(validators=[validate_embedding])
    text = models.TextField()
    metadata = models.JSONField(null=True, blank=True)
    object_id = models.CharField(max_length=255, null=True, blank=True)

    # allow null so that texts can be added without an object
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, null=True, blank=True
    )
    content_object = GenericForeignKey("content_type", "object_id")

    objects = VectorManager()

    class Meta:
        unique_together = ["content_type", "object_id"]
        verbose_name_plural = "vectors"

    @property
    def vector(self):
        return np.frombuffer(self.embedding, dtype=np.float32)

    def save(self, *args, **kwargs):
        if self.embedding is None:
            self.embedding = Vector.objects.embedding_fn(self.text).tobytes()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"Vector {self.id} with metadata {self.metadata}"


class SampleModel(models.Model):
    """A sample model to demonstrate how to use Vector model."""

    text = models.TextField()

    def get_vectordb_text(self):
        return self.text

    def get_vectordb_metadata(self):
        return {"text": self.text, "id": self.id, "field": "value"}

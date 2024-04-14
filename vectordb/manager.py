from __future__ import annotations

import logging
import os

from django.db import models

from .ann.indexes import HNSWIndex
from .queryset import VectorQuerySet
from .settings import vectordb_settings
from .utils import (
    create_vector_from_instance,
    create_vector_from_text,
    get_embedding_function,
)

# Get an instance of a logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VectorDB")


if not os.path.exists(os.path.dirname(vectordb_settings.DEFAULT_PERSISTENT_DIRECTORY)):
    os.makedirs(os.path.dirname(vectordb_settings.DEFAULT_PERSISTENT_DIRECTORY))


class VectorManager(models.Manager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index = None
        self.persistent_path = os.path.join(
            vectordb_settings.DEFAULT_PERSISTENT_DIRECTORY, "vector.index"
        )  # TODO: refactor coz this depends on internal knowledge of the index class

        embedding_fn, embedding_dim = get_embedding_function()
        self.embedding_dim = embedding_dim
        self.embedding_fn = embedding_fn

        if os.path.exists(self.persistent_path):
            self.index = HNSWIndex.load(self.persistent_path)

    def get_queryset(self):
        return VectorQuerySet(self.model, using=self._db)

    def add_text(self, id, text, metadata, embedding=None):
        """Add a text to the database and the index."""
        object_id = id

        return create_vector_from_text(
            manager=self,
            object_id=object_id,
            text=text,
            metadata=metadata,
            embedding=embedding,
        )

    def add_texts(self, ids, texts, metadata, embeddings=None):
        if embeddings is None:
            embeddings = self.embedding_fn(texts)
        vectors = [
            self.add_text(id, text, meta, embedding)
            for id, text, meta, embedding in zip(ids, texts, metadata, embeddings)
        ]
        return vectors

    def add_instance(self, instance):
        return create_vector_from_instance(manager=self, instance=instance)

    def add_instances(self, instances):
        return [self.add_instance(instance) for instance in instances]

    def search(self, *args, **kwargs):
        return self.get_queryset().search(*args, **kwargs)

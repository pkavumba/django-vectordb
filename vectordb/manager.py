from __future__ import annotations

import importlib
import os
import logging
import time

import numpy as np
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.utils import IntegrityError

from .ann.indexes import HNSWIndex
from .queryset import VectorQuerySet
from .utils import (
    serializer,
    get_embedding_function,
    create_vector_from_instance,
    create_vector_from_text,
    populate_index,
)
from .validators import validate_vector_data

# Get an instance of a logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


EMBEDDING_FN = getattr(settings, "EMBEDDING_FN", None)
EMBEDDING_DIM = getattr(settings, "EMBEDDING_DIM", None)

if EMBEDDING_FN is not None and EMBEDDING_DIM is None:
    raise ValueError("EMBEDDING_FN is set but EMBEDDING_DIM is not set")

PERSISTENT_PATH = getattr(
    settings,
    "PERSISTENT_PATH",
    os.path.join(settings.BASE_DIR, ".vectordb", "hnsw_index.bin"),
)

if not os.path.exists(os.path.dirname(PERSISTENT_PATH)):
    os.makedirs(os.path.dirname(PERSISTENT_PATH))


class VectorManager(models.Manager):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.index = None
        self.persistent_path = PERSISTENT_PATH


        logger.info("Loading the embedding function. This may take a few minutes the first time it runs as it downloads the wieghts for the model.")
        start = time.time()

        embedding_fn, embedding_dim = get_embedding_function()
        self.embedding_dim = EMBEDDING_DIM or embedding_dim
        self.embedding_fn = embedding_fn

        if os.path.exists(self.persistent_path):
            self.index = HNSWIndex.load(self.persistent_path)
        else:
            vector_count = self.count()
            if vector_count > 10_000:
                self.index = HNSWIndex(
                    max_elements=int(vector_count * 1.3), dim=self.embedding_dim
                )
        logger.info(f"Loading the weights has been completed in {time.time() - start} seconds")

    def get_queryset(self):
        return VectorQuerySet(self.model, using=self._db)

    def add_text(self, id, text, metadata, embedding=None):
        """Add a text to the database and the index."""
        object_id = id
        if not embedding:
            embedding = self.embedding_fn(text)

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

    def create(self, *args, **kwargs):
        text = kwargs.pop("text", None)
        embedding = kwargs.pop("embedding", None)
        metadata = kwargs.pop("metadata", None)
        content_object = kwargs.pop("content_object", None)
        object_id = kwargs.pop("object_id", None)

        validate_vector_data(
            manager=self,
            text=text,
            embedding=embedding,
            content_object=content_object,
            object_id=object_id,
        )

        # Get embeddings if text is provided and no embeddings are given
        if text is not None and embedding is None:
            embedding = self.embedding_fn(text)

        # Get metadata if content_object is provided and no metadata is given
        if content_object is not None and metadata is None:
            if hasattr(content_object, "serializer"):
                metadata = content_object.serializer()
            else:
                metadata = serializer(content_object)

        if content_object is None and object_id:
            kwargs.update({"object_id": object_id})

        # Update the kwargs with the obtained values
        kwargs.update(
            {
                "text": text,
                "embedding": embedding.tobytes(),
                "metadata": metadata,
                "content_object": content_object,
            }
        )

        # Create the object with the updated kwargs
        vector = super().create(*args, **kwargs)

        # hacky fix for the object_id not being set
        # for some reason the object_id is not set when using the create method
        if object_id and not vector.object_id:
            vector.object_id = object_id
            vector.save()
        vector_count = self.count()

        if vector_count > 10000:
            if self.index is None:
                self.index = HNSWIndex(
                    max_elements=vector_count + 1000, dim=self.embedding_dim
                )
                populate_index()
            else:
                self.index.add_vector(vector)

        if self.index:
            self.index.add_vector(vector)

        return vector

    def search(self, *args, **kwargs):
        return self.get_queryset().search(*args, **kwargs)

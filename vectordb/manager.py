from __future__ import annotations

import os
import logging
import time
from django.conf import settings
from django.db import models

from .ann.indexes import HNSWIndex
from .queryset import VectorQuerySet
from .utils import (
    get_embedding_function,
    create_vector_from_instance,
    create_vector_from_text,
)

# Get an instance of a logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VectorDB")


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

        logger.info(
            "Loading the embedding function. This may take a few minutes the first time it runs as it downloads the wieghts for the model."
        )
        start = time.time()

        embedding_fn, embedding_dim = get_embedding_function()
        self.embedding_dim = EMBEDDING_DIM or embedding_dim
        self.embedding_fn = embedding_fn

        if os.path.exists(self.persistent_path):
            self.index = HNSWIndex.load(self.persistent_path)

        logger.info(
            f"Loading the weights has been completed in {time.time() - start} seconds"
        )

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

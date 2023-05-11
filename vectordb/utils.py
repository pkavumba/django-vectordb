from __future__ import annotations

import importlib
import json
import logging
import os

import numpy as np
from django.conf import settings
from django.core.serializers import serialize
from django.db import models

from vectordb.settings import vectordb_settings

from .validators import validate_vector_data

try:
    import celery

    from . import tasks

    has_celery = True
    # check if celery settings are configured
    if not hasattr(settings, "CELERY_BROKER_URL"):
        raise ImportError

except ImportError:
    has_celery = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def flatten_object_json(serialized_data):
    flattened_data = {}

    # Add the model and primary key information
    flattened_data["model"] = serialized_data["model"]
    flattened_data["pk"] = serialized_data["pk"]

    # Add the fields from the nested JSON
    for field_name, field_value in serialized_data["fields"].items():
        flattened_data[field_name] = field_value

    return flattened_data


def serializer(obj):
    data = json.loads(
        serialize(
            "json",
            [
                obj,
            ],
        )
    )[0]
    return flatten_object_json(data)


def create_vector_from_instance(manager, instance):
    embedding_fn, embedding_dim = get_embedding_function()
    if hasattr(instance, "get_vectordb_text"):
        text = instance.get_vectordb_text()
    else:
        raise ValueError(
            f"Object of class {instance.__class__.__name__} must have a get_vectordb_text method."
        )

    if hasattr(instance, "get_vectordb_metadata"):
        metadata = instance.get_vectordb_metadata()
    else:
        metadata = serializer(instance)

    embedding = embedding_fn(text)

    return manager.create(
        content_object=instance,
        text=text,
        embedding=embedding.astype("float32").tobytes(),
        metadata=metadata,
    )


def create_vector_from_text(
    manager: models.Manager,
    text,
    metadata=None,
    object_id=None,
    content_type=None,
    embedding=None,
):
    embedding_fn, embedding_dim = get_embedding_function()

    if embedding is None and not has_celery:
        embedding = embedding_fn(text)

    validate_vector_data(
        manager=manager,
        text=text,
        content_object=None,
        object_id=object_id,
        embedding=embedding,
    )

    vector = manager.create(
        text=text,
        metadata=metadata,
        embedding=embedding.astype("float32").tobytes(),
        object_id=object_id,
    )

    if embedding is not None and has_celery:
        embedding = tasks.create_vector.delay(text)

    return vector


def get_embedding_function():
    embedding_fn = vectordb_settings.DEFAULT_EMBEDDING_CLASS(
        model_name=vectordb_settings.DEFAULT_EMBEDDING_MODEL
    )
    embedding_dim = vectordb_settings.DEFAULT_EMBEDDING_DIMENSION
    return embedding_fn, embedding_dim


def _populate_index(manager: models.Manager):
    vectors = manager.only("id", "embedding").all()
    vector_count = vectors.count()

    ids_list = []
    embeddings_list = []
    for vector in vectors:
        ids_list.append(vector.id)
        embeddings_list.append(vector.embedding)
    embeddings = np.frombuffer(b"".join(embeddings_list)).reshape(vector_count, -1)
    manager.index.add(embeddings=embeddings, ids=np.array(ids_list))


def populate_index(manager: models.Manager):
    if has_celery:
        tasks.populate_index.delay()
    else:
        _populate_index(manager=manager)

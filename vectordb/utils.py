from __future__ import annotations

import json
import logging
from collections import defaultdict

import numpy as np
from django.conf import settings
from django.core.serializers import serialize
from django.db import models

from vectordb.settings import vectordb_settings

from .validators import validate_vector_data

try:
    import celery  # noqa

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
            f"Object of class {instance.__class__.__name__} must have a "
            "get_vectordb_text method."
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
        embedding=np.array(embedding).astype("float32").tobytes(),
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


def rrf(*args, k=60):
    """
    Apply Reciprocal Rank Fusion (RRF) on multiple sorted lists of dictionaries.

    This function takes a variable number of sorted lists, each containing dictionaries
    with at least an 'id' field. It calculates the RRF score for each document and
    aggregates the scores across all lists. The final list is sorted by 'rrf_score' in
    descending order. The RRF score is calculated using the formula: 1 / (k + rank),
    where the rank is the position of the document in the sorted list.

    Args:
        *args: Variable number of sorted lists. Each list contains dictionaries with at
            least an 'id' field.
        k (int): The constant in the RRF formula. Default is 60.

    Returns:
        list: A list of dictionaries, sorted by 'rrf_score' in descending order, each
            containing the RRF score along with the original document fields.
    """
    # Dictionary to hold the cumulative RRF scores and other fields for each document
    rrf_scores = defaultdict(lambda: {"rrf_score": 0.0})

    # Iterate over each list passed as an argument
    for sorted_list in args:
        assert isinstance(sorted_list, list), "All positional arguments must be lists."
        # Start enumerate from 1 and avoid extra 1 in RRF formula
        for rank, item in enumerate(sorted_list, start=1):
            doc_id = item["id"]

            # If it's the first encounter of this doc_id, add all fields (excluding 'id')
            if "id" not in rrf_scores[doc_id]:
                rrf_scores[doc_id].update(item)

            # Apply the RRF formula: 1 / (k + rank) without adding extra 1 in rank
            rrf_scores[doc_id]["rrf_score"] += 1 / (k + rank)

    # Convert the dictionary to a list and sort by 'rrf_score' in descending order
    sorted_results = sorted(
        rrf_scores.values(), key=lambda x: x["rrf_score"], reverse=True
    )

    return sorted_results

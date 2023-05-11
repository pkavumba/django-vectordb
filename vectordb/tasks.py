from __future__ import annotations

from typing import Optional

import numpy as np
from celery import shared_task
from django.contrib.contenttypes.models import ContentType
from django.db import models

from .models import Vector
from .utils import get_embedding_function


@shared_task
def create_vector(vector_id: int) -> Vector:
    embedding_fn, embedding_dim = get_embedding_function()
    vector = Vector.objects.get(id=vector_id)
    vector.embedding = embedding_fn(vector.text).tobytes()
    vector.save()

    add_vector_to_index.delay(vector_id)

    return vector


@shared_task
def add_vector_to_index(vector_id: int):
    if Vector.objects.index is None:
        return

    vector = Vector.objects.only("id", "embedding").get(id=vector_id)
    embeddings = np.frombuffer(vector.embedding).reshape(1, -1)
    Vector.objects.index.add(embeddings=embeddings, ids=np.array([vector.id]))


@shared_task
def populate_index():
    if Vector.objects.index is None:
        return

    vectors = Vector.objects.only("id", "embedding").all()
    vector_count = vectors.count()

    ids_list = []
    embeddings_list = []
    for vector in vectors:
        ids_list = ids_list.append(vector.id)
        embeddings_list.append(vector.embedding)
    embeddings = np.frombuffer(b"".join(embeddings_list)).reshape(vector_count, -1)
    Vector.objects.index.add(embeddings=embeddings, ids=np.array(ids_list))


@shared_task
def update_index_all():
    populate_index.delay()

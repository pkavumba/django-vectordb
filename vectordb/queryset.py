from __future__ import annotations

import logging
import time

import numpy as np
from django.contrib.contenttypes.models import ContentType
from django.db import models

from vectordb.settings import vectordb_settings

from .ann.indexes import BFIndex, HNSWIndex

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(" VectorDB ")


class VectorQuerySet(models.QuerySet):
    def _get_related_vectors(
        self, query_embeddings, vectors, k: int | None = None, ids_list=None
    ):
        if k is None:
            k = vectordb_settings.DEFAULT_MAX_N_RESULTS
        manager = self.model.objects
        vector_count = len(vectors)
        # k cannot be greater than the number of vectors. Don't raise an error
        k = min(k, vector_count)

        if vector_count == 0:
            return self.none()

        embeddings_list = [vector.embedding for vector in vectors]
        embeddings = np.frombuffer(b"".join(embeddings_list), dtype=np.float32).reshape(
            vector_count, -1
        )

        if vector_count < 10_000:
            index = BFIndex(
                max_elements=vector_count,
                dim=vectordb_settings.DEFAULT_EMBEDDING_DIMENSION,
                space=vectordb_settings.DEFAULT_EMBEDDING_SPACE,
                should_not_cache=True,
            )
            index.add(embeddings, ids=ids_list)
            labels, distances = index.search(query_embeddings, k)
        else:
            if manager.index is None:
                manager.index = HNSWIndex(
                    max_elements=vector_count,
                    dim=vectordb_settings.DEFAULT_EMBEDDING_DIMENSION,
                    space=vectordb_settings.DEFAULT_EMBEDDING_SPACE,
                )
                manager.index.add(embeddings, ids=ids_list)

            labels, distances = manager.index.search(
                query_embeddings, k, ids__in=ids_list
            )
        labels: list[int] = labels[0].tolist()
        distances: list[float] = distances[0].tolist()

        # Annotate queryset with distances and sort by descending order
        queryset = self.filter(id__in=labels)

        queryset = queryset.annotate(
            distance=models.Case(
                *[
                    models.When(id=label, then=models.Value(distance))
                    for label, distance in zip(labels, distances)
                ],
                default=models.Value(0.0),
                output_field=models.FloatField(),
            )
        )

        return queryset.order_by("distance")

    def related_text(self, text: str, k: int | None = None):
        vectors = self
        ids_list = [vector.id for vector in vectors]
        query_embeddings = self.model.objects.embedding_fn([text])
        return self._get_related_vectors(query_embeddings, vectors, k, ids_list)

    def related_objects(self, model_object, k: int | None = None):
        content_type = ContentType.objects.get_for_model(model_object)

        if self.filter(content_type=content_type, object_id=model_object.id).exists():
            query_object = self.get(
                content_type=content_type, object_id=model_object.id
            )
            query_embeddings = np.frombuffer(
                query_object.embedding, dtype=np.float32
            ).reshape(1, -1)
        else:
            query_embeddings = self.model.objects.embedding_fn(model_object.get_text())

        vectors = self.filter(content_type=content_type).exclude(
            object_id=model_object.id, content_type=content_type
        )
        ids_list = [vector.id for vector in vectors]
        return self._get_related_vectors(query_embeddings, vectors, k, ids_list)

    def search(self, query, k: int | None = None):
        if isinstance(query, models.Model):
            start = time.time()
            results = self.related_objects(query, k=k)
            results.search_time = time.time() - start
            logger.info(f"Search took {1000*(time.time() - start)}ms")
            return results

        if isinstance(query, str):
            start = time.time()
            results = self.related_text(query, k=k)
            logger.info(f"Search took  {1000*(time.time() - start)}ms")
            results.search_time = time.time() - start
            return results
        else:
            raise ValueError("Query must be a model instance or string")

    def related(self, *args, **kwargs):
        return self.search(*args, **kwargs)

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


def _validate_option_search_args(k, content_type, unwrap):
    # validate k
    if k is not None and not isinstance(k, int):
        logger.warning(f"k must be an integer, but found {k} of type {type(k)}")

    # validate unwrap
    if unwrap and content_type is None:
        logger.warning(
            "unwrap=True and content_type=None. Unwrapped objects may contain any content_type"
        )
    # validate content_type
    if content_type is not None:
        if isinstance(content_type, ContentType):
            pass
        elif isinstance(content_type, str):
            # string can either be model name or app_label.model
            content_type = content_type.lower()
            if "." in content_type:
                content_parts = content_type.split(".")
                if len(content_parts) == 2:
                    app_label = content_parts[0]
                    model = content_parts[1]
                    content_type = ContentType.objects.get(
                        app_label=app_label, model=model
                    )
                else:
                    logger.warning(
                        f"Expected content_type to be in the format app_label.model, but found {content_type}"
                    )
                    content_type = None

            else:
                content_type = ContentType.objects.get(model=content_type)
        elif isinstance(content_type, int):
            content_type = ContentType.objects.get(id=content_type)
        elif isinstance(content_type, models.Model):
            content_type = ContentType.objects.get_for_model(content_type)
        elif issubclass(content_type, models.Model):
            content_type = ContentType.objects.get(
                app_label=content_type._meta.app_label,
                model=content_type._meta.model_name,
            )
        else:
            content_type = None
            logger.warning("content_type must be a ContentType instance")

    return k, content_type, unwrap


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

    def related_text(
        self,
        text: str,
        k: int | None = None,
        *,
        content_type: str | int | models.Model | ContentType | None = None,
        unwrap: bool = False,
    ):
        """Return the k most similar entries to the given text

        Args:
            text (str): The text to search for
            k (int, optional): The number of results to return. Defaults to None.
            content_type (str, int, models.Model, ContentType, optional): The content type to filter by. Defaults to None.
            unwrap (bool, optional): If True, return the actual model instances instead of the vector instances. Defaults to False.
        """
        k, content_type, unwrap = _validate_option_search_args(
            k=k, content_type=content_type, unwrap=unwrap
        )
        vectors = self

        if content_type is not None:
            vectors = vectors.filter(content_type=content_type)
            ids_list = [vector.id for vector in vectors]
        else:
            ids_list = [vector.id for vector in vectors]

        query_embeddings = self.model.objects.embedding_fn([text])

        # measure vectordb search time
        start = time.time()
        results = self._get_related_vectors(query_embeddings, vectors, k, ids_list)
        results.search_time = time.time() - start
        logger.info(f"Search took {1000*(time.time() - start)}ms")

        if unwrap:
            results = results.unwrap()
        return results

    def related_objects(
        self,
        model_object,
        k: int | None = None,
        *,
        content_type: str | int | models.Model | ContentType | None = None,
        unwrap: bool = False,
    ):
        """Return the k most similar entries to the given model instance.

        Args:
            model_object (models.Model): The model instance to search for
            k (int, optional): The number of results to return. Defaults to None.
            content_type (str, int, models.Model, ContentType, optional): The content type to filter by. Defaults to None.
            unwrap (bool, optional): If True, return the actual model instances instead of the vector instances. Defaults to False.
        """

        k, content_type, unwrap = _validate_option_search_args(
            k=k, content_type=content_type, unwrap=unwrap
        )

        # An object can only be related to types of itself
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

        # measure vectordb search time
        start = time.time()
        results = self._get_related_vectors(query_embeddings, vectors, k, ids_list)
        results.search_time = time.time() - start
        logger.info(f"Search took {1000*(time.time() - start)}ms")

        if unwrap:
            results = results.unwrap()
        return results

    def search(
        self,
        query,
        k: int | None = None,
        *,
        content_type: str | int | models.Model | ContentType | None = None,
        unwrap: bool = False,
    ):
        """
        Search for similar vectors in the queryset
        Args:
            query: A string or a model instance
            k: Number of results to return
            content_type: A ContentType instance or a model class
            unwrap: If True, return the actual model instances instead of the vector instances.
                This breaks the queryset chaining.
        Returns:
            A list of model instances or vector instances
        """

        # search
        if isinstance(query, models.Model):
            results = self.related_objects(
                query, k=k, content_type=content_type, unwrap=unwrap
            )
        elif isinstance(query, str):
            results = self.related_text(
                query, k=k, content_type=content_type, unwrap=unwrap
            )
        else:
            raise ValueError("Query must be a model instance or string")

        return results

    def related(self, *args, **kwargs):
        return self.search(*args, **kwargs)

    def unwrap(self):
        """Return the actual model instances instead of the vector instances.

        This breaks the queryset chaining.

        Returns:
            A list of model instances
        """
        return [
            result.content_object
            for result in self
            if result.content_object is not None
        ]

from __future__ import annotations
from typing import Optional
import numpy as np
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.db import models

import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def validate_vector_data(
    manager: models.Manager,
    *,
    text: Optional[str],
    embedding: Optional[np.array],
    content_object: models.Model,
    object_id: Optional[str | int] = None,
):
    logger.warning("Validating")
    # Check if either text or content_object is provided
    if text is None and content_object is None:
        raise ValidationError("Either text or content_object should be provided")

    # If text is not provided but content_object is provided, get text from content_object
    if text is None and content_object is not None:
        if hasattr(content_object, "get_text"):
            text = content_object.get_text()
        else:
            raise ValidationError("The content_object should have a 'get_text' method")

    # If content_object is not provided, object_id should be provided
    if content_object is None and object_id is None:
        raise ValidationError(
            "If content_object is not provided, object_id should be provided"
        )

    if (
        content_object is not None
        and object_id is not None
        and content_object.id != object_id
    ):
        raise ValidationError(
            "The content_object id should be the same as the object_id"
        )

    if (
        content_object is None
        and object_id
        and manager.filter(content_type__isnull=True, object_id=object_id).exists()
    ):
        raise IntegrityError(f"Vector with id {object_id} already exists.")

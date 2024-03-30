"""Cohere embeddings."""

from __future__ import annotations

from typing import Literal

import numpy as np
from django.conf import settings

from ..settings import vectordb_settings

# support those setting the key in vectordb_settings or django settings
if not hasattr(settings, "COHERE_API_KEY"):
    setattr(settings, "COHERE_API_KEY", vectordb_settings.COHERE_API_KEY)

try:
    import cohere  # noqa
except ImportError:
    raise ImportError(
        "Cohere API is not installed. Please install cohere package. Or run `$ pip install cohere`"
    )

INPUT_TYPE = Literal["search_document", "search_query"]


class CohereEmbeddings:
    """Cohere embeddings."""

    def __init__(self, model_name="embed-multilingual-v3.0"):
        """Initialize Cohere embeddings.

        Args:
            model_name (str, optional): Cohere model name. Defaults to "embed-multilingual-v3.0".
        """
        if not hasattr(settings, "COHERE_API_KEY"):
            raise ValueError("`COHERE_API_KEY` is not set in Django settings.")
        self.client = cohere.Client(api_key=settings.COHERE_API_KEY)
        self.model = model_name

    def get_embedding(
        self, text: str | list[str], input_type: INPUT_TYPE = "search_document"
    ) -> np.ndarray:
        """Get embeddings for text.

        Args:
            text (str | list[str]): Text to embed.
            input_type (Literal["search_document", "search_query"]): Input type.
                Defaults to "search_document".

        Returns:
            np.ndarray: Embeddings.
        """
        if isinstance(text, list):
            response = self.client.embed(
                texts=text, input_type=input_type, model=self.model
            )
            return np.array(response.embeddings, dtype=np.float32)
        elif isinstance(text, str):
            text = text.replace("\n", " ")
            response = self.client.embed(
                texts=[text], input_type=input_type, model=self.model
            )
            return np.array(response.embeddings[0], dtype=np.float32)
        else:
            raise ValueError("`text` must be a string or a list of strings.")

    def __call__(
        self, text: str | list[str], input_type: str = "search_document"
    ) -> np.ndarray:
        """Get embeddings for text.

        Args:
            text (str | list[str]): Text to embed.
            input_type (Literal["search_document", "search_query"]): Input type.
                Defaults to "search_document".

        Returns:
            np.ndarray: Embeddings.
        """
        return self.get_embedding(text, input_type)

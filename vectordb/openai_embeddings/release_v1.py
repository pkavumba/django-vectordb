from __future__ import annotations

import numpy as np
from django.conf import settings

try:
    import openai  # noqa
    from openai import OpenAI
except ImportError:
    openai = None

from ..settings import vectordb_settings

# support those setting the key in vectordb_settings or django settings

if not hasattr(settings, "OPENAI_API_KEY"):
    setattr(settings, "OPENAI_API_KEY", vectordb_settings.OPENAI_API_KEY)


class OpenAIEmbeddings:
    def __init__(self, model_name="text-embedding-ada-002"):
        if not hasattr(settings, "OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY is not set in Django settings.")
        if openai is None:
            raise ImportError(
                "OpenAI API is not installed. Please install openai package. Or run `$ pip install openai`"  # noqa
            )

        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = model_name

    def get_embedding(self, text: str) -> np.ndarray:
        text = text.replace("\n", " ")
        response = self.client.embeddings.create(input=[text], model=self.model)
        raw_embedding = response.data[0].embedding
        return np.array(raw_embedding, dtype=np.float32)

    def __call__(self, text: str | list[str]) -> np.ndarray:
        if isinstance(text, list):
            return [self.get_embedding(t) for t in text]
        return self.get_embedding(text)

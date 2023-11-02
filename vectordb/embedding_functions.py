from __future__ import annotations

import numpy as np
from django.conf import settings

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

try:
    import openai
except ImportError:
    openai = None


class SentenceTransformerEncoder:
    _instances: dict[str, SentenceTransformerEncoder] = {}

    def __new__(cls, model_name: str = "all-MiniLM-L6-v2", *args, **kwargs):
        if model_name not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[model_name] = instance
        return cls._instances[model_name]

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if SentenceTransformer is None:
            raise ImportError(
                "SentenceTransformer is not installed. Please install sentence-transformers package."  # noqa
                " Or run `$ pip install sentence-transformers`"
            )
        if not hasattr(self, "model"):
            self.model = SentenceTransformer(model_name)

    def __call__(self, texts: list[str]) -> np.ndarray:
        return self.model.encode(texts, convert_to_numpy=True)


class OpenAIEmbeddings:
    def __init__(self, model_name="text-embedding-ada-002"):
        if not hasattr(settings, "OPENAI_API_KEY"):
            raise ValueError("OPENAI_API_KEY is not set in Django settings.")
        if openai is None:
            raise ImportError(
                "OpenAI API is not installed. Please install openai package. Or run `$ pip install openai`"  # noqa
            )
        openai.api_key = settings.OPENAI_API_KEY
        self.model = model_name

    def get_embedding(self, text: str) -> np.ndarray:
        text = text.replace("\n", " ")
        response = openai.Embedding.create(input=[text], model=self.model)
        raw_embedding = response["data"][0]["embedding"]
        return np.array(raw_embedding, dtype=np.float32)

    def __call__(self, text: str | list[str]) -> np.ndarray:
        if isinstance()(text, list):
            return [self.get_embedding(t) for t in text]
        return self.get_embedding(text)

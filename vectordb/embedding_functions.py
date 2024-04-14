from __future__ import annotations

import logging
import time

import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

try:
    import openai  # noqa
    from openai_embeddings import OpenAIEmbeddings  # noqa
except ImportError:
    openai = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("VectorDB")


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
            logger.info(
                "Loading the weights for the embedding model. This may take a few seconds the first"
                " time it runs because it downloads the weights and caches them."
            )
            start = time.time()
            self.model = SentenceTransformer(model_name)
            logger.info(
                f"Loading the weights has been completed in {time.time() - start} seconds"
            )

    def __call__(self, texts: list[str]) -> np.ndarray:
        return self.model.encode(texts, convert_to_numpy=True)

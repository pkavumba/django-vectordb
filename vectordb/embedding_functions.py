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

from .settings import vectordb_settings

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
        self.model_name = model_name

        # sanity check and give informative error message
        if SentenceTransformer is None:
            raise ImportError(
                "SentenceTransformer is not installed. Please install sentence-transformers package."  # noqa
                " Or run `$ pip install sentence-transformers`"
            )

        if not hasattr(self, "model"):
            if vectordb_settings.LOAD_EMBEDDING_MODEL_ON_STARTUP:
                self.model = self._load_model(model_name)
            else:
                logger.warning(
                    "The model will be loaded on the first call to the embedding function. "
                    "Because the setting 'LOAD_EMBEDDING_MODEL_ON_STARTUP' is set to False."
                )

    def _load_model(self, model_name: str) -> SentenceTransformer:
        logger.info(
            "Loading the weights for the embedding model. This may take a few seconds the first"
            " time it runs because it downloads the weights and caches them."
        )
        start = time.time()
        model = SentenceTransformer(model_name)
        logger.info(
            f"Loading the weights has been completed in {time.time() - start} seconds"
        )
        return model

    def __call__(self, texts: list[str]) -> np.ndarray:
        if getattr(self, "model", None) is None:
            self.model = self._load_model(self.model_name)
        return self.model.encode(texts, convert_to_numpy=True)

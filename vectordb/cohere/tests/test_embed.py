import numpy as np
import pytest

from ...cohere.embed import CohereEmbeddings


@pytest.mark.skip(reason="Test only works with Cohere API key.")
def test_embeddings():
    embedding_fn = CohereEmbeddings()
    text = "Hello World!"
    embedding = embedding_fn(text)
    assert isinstance(embedding, np.ndarray)
    assert embedding.shape == (1024,)

    embedding = embedding_fn([text])
    assert isinstance(embedding, np.ndarray)
    assert embedding.shape == (1, 1024)

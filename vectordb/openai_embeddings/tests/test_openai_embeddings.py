import numpy as np
import pytest

from ...openai_embeddings import OpenAIEmbeddings


@pytest.mark.skip(reason="Test only works with OpenAI API key.")
def test_embeddings():
    embedding_fn = OpenAIEmbeddings()
    embedding = embedding_fn("Hello World!")
    assert isinstance(embedding, np.ndarray)
    assert embedding.shape == (1536,)

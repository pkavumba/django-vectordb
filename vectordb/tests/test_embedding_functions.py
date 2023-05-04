import pytest
from vectordb.embedding_functions import SentenceTransformerEncoder


@pytest.fixture
def encoder():
    return SentenceTransformerEncoder()


def test_singleton_pattern(encoder):
    encoder2 = SentenceTransformerEncoder()
    assert encoder is encoder2


def test_model_initialization(encoder):
    assert hasattr(encoder, "model")


@pytest.mark.parametrize(
    "texts, expected_length",
    [
        (["Hello world"], 1),
        (["Hello world", "This is a test"], 2),
    ],
)
def test_call_method(encoder, texts, expected_length):
    embeddings = encoder(texts)
    assert len(embeddings) == expected_length
    assert embeddings.shape == (expected_length, 384)

import os
import json
import pytest
import numpy as np
from django.conf import settings
from vectordb.ann.indexes import BFIndex, HNSWIndex

nb = 100
nq = 10
d = 64


@pytest.fixture
def bf_index():
    return BFIndex(dim=d, max_elements=nb, space="l2")


@pytest.fixture
def data():
    embeddings = np.random.rand(nb, d)
    ids = np.arange(nb)
    return {"embeddings": embeddings, "ids": ids}


@pytest.mark.django_db
def test_bfindex_singleton():
    index1 = BFIndex(max_elements=1000, dim=128, space="l2")
    index2 = BFIndex(max_elements=1000, dim=128, space="l2")
    assert index1 is index2


@pytest.mark.django_db
def test_hnswindex_singleton():
    index1 = HNSWIndex(
        dim=128, max_elements=1000, M=16, ef_construction=200, ef=50, space="l2"
    )
    index2 = HNSWIndex(
        dim=128, max_elements=1000, M=16, ef_construction=200, ef=50, space="l2"
    )
    assert index1 is index2


def test_bf_index_init(bf_index):
    assert bf_index.dim == d
    assert bf_index.space == "l2"
    assert bf_index.max_elements == nb


def test_bf_index_add(bf_index, data):
    bf_index.add(**data)
    assert bf_index.size == nb


def test_bf_index_search(bf_index, data):
    bf_index.add(**data)
    query = np.random.rand(nq, d)
    result_ids, result_distances = bf_index.search(query, k=5)
    assert len(result_ids) == nq
    assert len(result_ids[0]) == 5


def test_bf_index_persist(tmpdir, bf_index, data):
    bf_index.add(**data)
    directory = str(tmpdir.join("bf_index"))
    bf_index.persist(directory)


def test_bf_index_persist_load(tmpdir, bf_index, data):
    bf_index.add(**data)
    directory = str(tmpdir.join("bf_index"))
    bf_index.persist(directory)
    loaded_bf_index = BFIndex.load(directory)
    assert loaded_bf_index.dim == bf_index.dim
    assert loaded_bf_index.space == bf_index.space


# HNSWIndex tests
@pytest.fixture
def hnsw_index():
    return HNSWIndex(dim=d, max_elements=nb, space="l2")


def test_hnsw_index_init(hnsw_index):
    assert hnsw_index.dim == d
    assert hnsw_index.space == "l2"


def test_hnsw_index_add(hnsw_index, data):
    hnsw_index.add(**data)
    assert hnsw_index.size == nb


def test_hnsw_index_search(hnsw_index, data):
    hnsw_index.add(**data)
    query = np.random.rand(nq, d)
    result_ids, result_distances = hnsw_index.search(query, k=1)
    assert len(result_ids) == nq
    assert len(result_ids[0]) == 1


def test_hnsw_index_persist(tmpdir, hnsw_index):
    embeddings = np.random.rand(nb, d)
    ids = np.arange(nb)
    hnsw_index.add(embeddings, ids)
    directory = str(tmpdir.join("hnsw_index"))
    hnsw_index.persist(directory)


def test_hnsw_index_persist_load(tmpdir, hnsw_index):
    embeddings = np.random.rand(nb, d)
    ids = np.arange(nb)
    hnsw_index.add(embeddings, ids)
    directory = str(tmpdir.join("hnsw_index"))
    hnsw_index.persist(directory)
    loaded_hnsw_index = HNSWIndex.load(directory)
    assert loaded_hnsw_index.dim == hnsw_index.dim
    assert loaded_hnsw_index.space == hnsw_index.space

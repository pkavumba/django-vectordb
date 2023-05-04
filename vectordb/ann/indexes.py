from __future__ import annotations

import abc
import os
from typing import Any
import hnswlib
import numpy as np
import json

from . import AbstractIndex


class HSWNLibIndex(AbstractIndex):
    def __init__(self, dim, max_elements, space="l2", *args, **kwargs):
        self.dim = dim
        self.max_elements = max_elements
        self.space = space  # space can either be "l2" or "cosine"

    def __call__(self, *args, **kwargs):
        return self.search(*args, **kwargs)

    @property
    def size(self):
        return self.index.get_current_count()

    def add(self, embeddings, ids, replace_deleted=True):
        if self.size + len(ids) > self.max_elements:
            self.resize()
        self.index.add_items(embeddings, ids, replace_deleted=replace_deleted)
        return self

    def update(self, embeddings, ids, replace_deleted=True):
        self.index.add_items(embeddings, ids, replace_deleted=replace_deleted)
        return self

    def delete(self, ids):
        for id in ids:
            self.index.mark_deleted(id)
        return self

    def resize(self):
        size = int(self.index.get_current_count() * 1.2)
        self.index.resize_index(size)
        self.max_elements = size
        return self

    @classmethod
    def load(cls, directory):
        # Load the rest of the class attributes from the JSON file
        with open(directory + ".meta", "r") as f:
            data = json.load(f)

        instance = cls(**data)

        # Load the HNSWLib index using HNSWLib's own method
        instance.index.load_index(os.path.join(directory, "vector.index"))

        # Initialize the class with the loaded attributes
        return instance

    def reset(self):
        self.index.reset()
        return self


class BFIndex(HSWNLibIndex):
    def __init__(self, max_elements: int, dim: int, space="l2", *args, **kwargs):
        super().__init__(dim, max_elements, space)
        self.max_elements = max_elements
        self.index = hnswlib.BFIndex(space=self.space, dim=self.dim)
        self.init_index()

    @property
    def size(self):
        # BFIndex does not have a method to get the current count
        return self.max_elements

    def add(self, embeddings, ids=None):
        self.index.add_items(embeddings, ids)
        return self

    def init_index(self):
        self.index.init_index(max_elements=self.max_elements)
        return self

    @property
    def metadata(self):
        return {"dim": self.dim, "max_elements": self.max_elements, "space": self.space}

    def search(self, query, k=10, **kwargs):
        ids_in = kwargs.get("ids__in", None)
        ids_not_in = kwargs.get("ids__not_in", None)
        ef = kwargs.get("ef", None)

        filter_fn = None
        if ids_in is not None and ids_not_in is not None:
            filter_fn = lambda x: x in ids_in and x not in ids_not_in
        elif ids_in is not None:
            filter_fn = lambda x: x in ids_in
        elif ids_not_in is not None:
            filter_fn = lambda x: x not in ids_not_in

        if ef is not None:
            if type(self.index) == hnswlib.Index:
                self.index.set_ef(ef)
            else:
                ValueError("ef can only be set for HNSW Index")

        return self.index.knn_query(query, k, filter=filter_fn)

    def persist(self, directory):
        if not os.path.exists(directory):
            os.mkdir(directory)

        self.index.save_index(os.path.join(directory, "vector.index"))
        with open(directory + ".meta", "w") as f:
            json.dump(self.metadata, f)


class HNSWIndex(HSWNLibIndex):
    def __init__(
        self,
        dim: int,
        max_elements: int,
        index=None,
        M: int = 64,
        ef_construction: int = 128,
        ef: int = 50,
        space: str = "l2",
    ):
        super().__init__(max_elements, dim, space)
        self.dim = dim
        self.M = M
        self.ef_construction = ef_construction
        self.ef = ef
        self.max_elements = max_elements

        if index is None:
            self.index = hnswlib.Index(space=self.space, dim=self.dim)
            self.init_index()
        else:
            self.index = index

    def init_index(self):
        self.index.init_index(
            max_elements=self.max_elements,
            ef_construction=self.ef_construction,
            M=self.M,
            random_seed=42,
            allow_replace_deleted=True,
        )
        return self

    def search(self, query, k=10, **kwargs):
        ids_in = kwargs.get("ids__in", None)
        ids_not_in = kwargs.get("ids__not_in", None)
        ef = kwargs.get("ef", None)

        filter_fn = None
        if ids_in is not None and ids_not_in is not None:
            filter_fn = lambda x: x in ids_in and x not in ids_not_in
        elif ids_in is not None:
            filter_fn = lambda x: x in ids_in
        elif ids_not_in is not None:
            filter_fn = lambda x: x not in ids_not_in

        if ef is not None:
            if type(self.index) == hnswlib.Index:
                self.index.set_ef(ef)
            else:
                ValueError("ef can only be set for HNSW Index")

        if filter_fn is not None:
            #
            return self.index.knn_query(query, k, filter=filter_fn, num_threads=1)

        return self.index.knn_query(query, k, num_threads=-1)

    @property
    def metadata(self):
        return {
            "dim": self.dim,
            "max_elements": self.max_elements,
            "space": self.space,
            "M": self.M,
            "ef_construction": self.ef_construction,
            "ef": self.ef,
        }

    def persist(self, directory):
        if not os.path.exists(directory):
            os.mkdir(directory)

        self.index.save_index(os.path.join(directory, "vector.index"))
        with open(directory + ".meta", "w") as f:
            json.dump(self.metadata, f)

from __future__ import annotations

import abc

from .singleton import SingletonABCMeta


class AbstractIndex(abc.ABC, metaclass=SingletonABCMeta):
    @abc.abstractmethod
    def size(self):
        """Return the number of items in the index."""
        pass

    @abc.abstractmethod
    def add(self, embeddings, *args, **kwargs):
        """Add embeddings to the index."""
        pass

    @abc.abstractmethod
    def search(self, query, k=10, *args, **kwargs):
        """Search the index for the k nearest neighbors of the query."""
        pass

    @abc.abstractmethod
    def delete(self, ids, *args, **kwargs):
        """Exclude items from the index based on a condition."""
        pass

    @abc.abstractmethod
    def persist(self, directory):
        """Persist the index to a file."""
        pass

    @classmethod
    @abc.abstractmethod
    def load(cls, directory):
        """Load an index from a file."""
        pass

    @abc.abstractmethod
    def reset(self):
        """Reset the index to its initial state."""
        pass

from __future__ import annotations

from typing import Any


import abc


class SingletonMeta(type):
    _instances: dict[Any, Any] = {}

    def __call__(cls, *args, **kwargs):
        key = (cls,) + (tuple(args), tuple(sorted(kwargs.items())))
        if key not in cls._instances:
            cls._instances[key] = super().__call__(*args, **kwargs)
        return cls._instances[key]


class SingletonABCMeta(SingletonMeta, abc.ABCMeta):
    pass

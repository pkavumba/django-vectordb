from abc import ABC

from vectordb.ann import SingletonABCMeta


class TSingleton(ABC, metaclass=SingletonABCMeta):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


def test_singleton_meta():
    instance1 = TSingleton()
    instance2 = TSingleton()

    assert instance1 is instance2

    instance3 = TSingleton(1, 2, 3)
    instance4 = TSingleton(1, 2, 3)

    assert instance3 is instance4
    assert instance1 is not instance3

    instance5 = TSingleton(a=1, b=2)
    instance6 = TSingleton(a=1, b=2)

    assert instance5 is instance6
    assert instance1 is not instance5

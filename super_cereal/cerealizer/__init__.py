import abc
from typing import TypeVar, Generic

T = TypeVar('T')
V = TypeVar('V')


class Cerealizer(abc.ABC, Generic[T, V]):
    @abc.abstractmethod
    def serialize(self, obj: T) -> V:
        ...

    @abc.abstractmethod
    def deserialize(self, obj: V, t: T) -> T:
        ...

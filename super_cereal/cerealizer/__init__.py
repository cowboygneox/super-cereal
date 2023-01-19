import abc
from typing import TypeVar, Generic

T = TypeVar('T')
V = TypeVar('V')


class SerializationException(Exception):
    pass


class DeserializationException(Exception):
    pass


class Cerealizer(abc.ABC, Generic[T, V]):  # pragma: no cover
    @abc.abstractmethod
    def serialize(self, obj: T) -> V:
        pass

    @abc.abstractmethod
    def deserialize(self, obj: V, t: T) -> T:
        pass

import abc
import typing
from abc import ABC
from typing import TypeVar, Generic, Dict, Optional

T = TypeVar('T')
V = TypeVar('V')


class SerializationException(Exception):
    pass


class DeserializationException(Exception):
    pass


class ICerealizer(Generic[T, V], abc.ABC):  # pragma: no cover

    @abc.abstractmethod
    def serialize(self, obj: any, t: T = None) -> V:
        pass

    @abc.abstractmethod
    def deserialize(self, obj: V, t: T) -> T:
        pass


class ITypeRegistry(Dict[type, ICerealizer], abc.ABC):
    @property
    @abc.abstractmethod
    def default(self):
        return self.default


class Cerealizer(ICerealizer[T, V], ABC):
    def __init__(self, encryption_keys: Dict[str, bytes] = None):
        if encryption_keys is None:
            encryption_keys = {}
        self.encryption_keys = encryption_keys

    def add_registry(self, registry: Optional[ITypeRegistry]):
        self.registry = registry


class TheTypeRegistry(ITypeRegistry):
    def __init__(self) -> None:
        super().__init__()
        self.d: Dict[type, Cerealizer] = {}
        self._default = None

    @property
    def default(self):
        return self._default

    @default.setter
    def default(self, value):
        if self._default is not None:
            self._default.add_registry(None)

        self._default = value

        value.add_registry(self)

    def __contains__(self, item):
        return item in self.d

    def __getitem__(self, item):
        if item in self.d:
            return self.d[item]
        if typing.get_origin(item) in self.d:
            return self.d[typing.get_origin(item)]
        if type(item) in self.d:
            return self.d[type(item)]

        return self.default

    def __setitem__(self, key: type, value: Cerealizer):
        self.d[key] = value
        value.add_registry(self)

    def __delitem__(self, key):
        popped = self.d.pop(key)
        popped.add_registry(None)

    def __len__(self):
        return len(self.d) + 1

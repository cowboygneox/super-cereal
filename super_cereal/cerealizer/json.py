import json
import typing

from super_cereal.cerealizer import Cerealizer, T, TheTypeRegistry
from super_cereal.cerealizer.builtins import PassthruCerealizer, ListCerealizer, UnionCerealizer, DictCerealizer
from super_cereal.cerealizer.encryption import EncryptedCerealizer, Encrypted

JsonTypes = typing.Union[str, float, int, bool, type(None), list, dict]


class JsonCerealizer(Cerealizer[T, JsonTypes]):
    def __init__(self, encryption_keys: typing.Dict[str, bytes] = None):
        registry = TheTypeRegistry()
        registry[type(None)] = PassthruCerealizer()
        registry[str] = PassthruCerealizer()
        registry[float] = PassthruCerealizer()
        registry[int] = PassthruCerealizer()
        registry[bool] = PassthruCerealizer()
        registry[list] = ListCerealizer()
        registry[typing.List] = ListCerealizer()
        registry[typing.Union] = UnionCerealizer()

        if EncryptedCerealizer.enabled():
            registry[Encrypted] = EncryptedCerealizer(encryption_keys, self)

        registry.default = DictCerealizer()

        self.registry = registry

    def serialize(self, obj: any, expected_type: T = None) -> JsonTypes:
        if expected_type is None:
            expected_type = type(obj)

        if expected_type in self.registry:
            return self.registry[expected_type].serialize(obj, expected_type)
        if typing.get_origin(expected_type) in self.registry:
            return self.registry[typing.get_origin(expected_type)].serialize(obj, expected_type)

        return self.registry.default.serialize(obj, expected_type)

    def deserialize(self, obj: JsonTypes, t: T) -> T:
        if t in self.registry:
            return self.registry[t].deserialize(obj, t)
        if typing.get_origin(t) in self.registry:
            return self.registry[typing.get_origin(t)].deserialize(obj, t)

        return self.registry.default.deserialize(obj, t)


class JsonByteCerealizer(JsonCerealizer):

    def __init__(self, encryption_keys: typing.Dict[str, bytes] = None):
        super().__init__(encryption_keys)

    def serialize(self, obj: any, expected_type: T = None) -> bytes:
        return json.dumps(super().serialize(obj, expected_type)).encode()

    def deserialize(self, obj: bytes, t: T) -> T:
        return super().deserialize(json.loads(obj.decode()), t)

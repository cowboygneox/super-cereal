import base64
import dataclasses
import json
import typing
from typing import Generic, TypeVar, Dict

from super_cereal.cerealizer import Cerealizer, T

E = TypeVar('E')


@dataclasses.dataclass
class Encrypted(Generic[E]):
    key_id: str
    value: T


class EncryptedCerealizer(Cerealizer[Encrypted[E], Dict[str, E]]):

    def __init__(self, keys: Dict[str, bytes], value_cerealizer: Cerealizer) -> None:
        super().__init__()
        self.keys = keys
        self.value_cerealizer = value_cerealizer

    def serialize(self, obj: Encrypted[E], t: T = None) -> Dict[str, E]:
        from cryptography.fernet import Fernet
        f = Fernet(self.keys[obj.key_id])

        if t:
            t = typing.get_args(obj)
        if not t:
            t = type(obj.value)

        return {
            'key_id': obj.key_id,
            'value': base64.b64encode(f.encrypt(json.dumps(self.value_cerealizer.serialize(obj.value, t)).encode())).decode()
        }

    def deserialize(self, obj: Dict[str, E], t: Encrypted[E]) -> Encrypted[E]:
        from cryptography.fernet import Fernet
        f = Fernet(self.keys[obj['key_id']])

        t = typing.get_args(t)[0]

        decrypted = f.decrypt(base64.b64decode(obj['value'])).decode()
        payload = json.loads(decrypted)
        return Encrypted(key_id=obj['key_id'], value=self.value_cerealizer.deserialize(payload, t))

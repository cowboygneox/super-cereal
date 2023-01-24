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
        """
        https://pycryptodome.readthedocs.io/en/latest/src/cipher/modern.html?highlight=gcm#gcm-mode
        :param obj:
        :param t:
        :return:
        """
        from Crypto.Cipher import AES

        if t:
            t = typing.get_args(obj)
        if not t:
            t = type(obj.value)

        cipher = AES.new(self.keys[obj.key_id], AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(json.dumps(self.value_cerealizer.serialize(obj.value, t)).encode())

        return {
            'key_id': obj.key_id,
            'value': base64.b64encode(ciphertext).decode(),
            'tag': base64.b64encode(tag).decode(),
            'nonce': base64.b64encode(cipher.nonce).decode()
        }

    def deserialize(self, obj: Dict[str, E], t: Encrypted[E]) -> Encrypted[E]:
        from Crypto.Cipher import AES

        t = typing.get_args(t)[0]

        cipher = AES.new(self.keys[obj['key_id']], AES.MODE_GCM, nonce=base64.b64decode(obj['nonce']))
        plaintext = cipher.decrypt_and_verify(base64.b64decode(obj['value']), base64.b64decode(obj['tag']))

        payload = json.loads(plaintext)
        return Encrypted(key_id=obj['key_id'], value=self.value_cerealizer.deserialize(payload, t))

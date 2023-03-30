import base64
import dataclasses
import json
import typing
from typing import Generic, TypeVar, Dict

from super_cereal.cerealizer import Cerealizer, T

E = TypeVar('E')


@dataclasses.dataclass
class Encrypted(Generic[E]):
    """
    Container class for automatically encrypting during serialization and decrypting during deserialization.

    `value` will be None when initially set as None, or when the encryption key for `key_id` is not present.
    """
    key_id: str
    value: typing.Optional[E]

    def __str__(self):
        return 'Encrypted(***)'

    def __repr__(self):
        return f'Encrypted(key_id={self.key_id}, value=***)'


class EncryptedCerealizer(Cerealizer[Encrypted[E], Dict[str, E]]):

    def __init__(self, keys: Dict[str, bytes], value_cerealizer: Cerealizer) -> None:
        super().__init__(keys)
        self.value_cerealizer = value_cerealizer

    @staticmethod
    def enabled() -> bool:
        try:
            from Crypto.Cipher import AES
            return True
        except ImportError:
            return False

    def serialize(self, obj: Encrypted[E], t: T = None) -> Dict[str, E]:
        """
        https://pycryptodome.readthedocs.io/en/latest/src/cipher/modern.html?highlight=gcm#gcm-mode
        """
        from Crypto.Cipher import AES

        if t:
            t = typing.get_args(obj)
        if not t:
            t = type(obj.value)

        cipher = AES.new(self.encryption_keys[obj.key_id], AES.MODE_GCM)
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

        try:
            key_id = self.encryption_keys[obj['key_id']]
        except KeyError:
            return Encrypted(obj['key_id'], None)

        cipher = AES.new(key_id, AES.MODE_GCM, nonce=base64.b64decode(obj['nonce']))
        plaintext = cipher.decrypt_and_verify(base64.b64decode(obj['value']), base64.b64decode(obj['tag']))

        payload = json.loads(plaintext)
        return Encrypted(key_id=obj['key_id'], value=self.value_cerealizer.deserialize(payload, t))

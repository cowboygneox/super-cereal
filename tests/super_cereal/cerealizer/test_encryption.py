import dataclasses

import pytest

from super_cereal.cerealizer.encryption import EncryptedCerealizer, Encrypted
from super_cereal.cerealizer.json import JsonCerealizer


@pytest.mark.parametrize('obj', ['stuff', 42, 12.552, True], ids=[str, int, float, bool])
def test_simple_serialization(obj: any):
    encryption = Encrypted[type(obj)](
        key_id='the_key',
        value=obj
    )

    key = b'6YPPnFEgjAoF-NFmtATGP9wNU0KGnqW2Lm9YP_FLm3s='

    cerealizer = EncryptedCerealizer({'the_key': key}, JsonCerealizer())

    serialized = cerealizer.serialize(encryption)
    assert cerealizer.deserialize(serialized, Encrypted[type(obj)]) == encryption


def test_object_serialization():
    @dataclasses.dataclass
    class TestClass:
        field1: str
        field2: int

    encryption = Encrypted[TestClass](
        key_id='the_key',
        value=TestClass('bogus', 3322)
    )

    key = b'6YPPnFEgjAoF-NFmtATGP9wNU0KGnqW2Lm9YP_FLm3s='

    cerealizer = EncryptedCerealizer({'the_key': key}, JsonCerealizer())

    serialized = cerealizer.serialize(encryption)
    assert cerealizer.deserialize(serialized, Encrypted[TestClass]) == encryption


def test_serializes_encrypted_object():
    @dataclasses.dataclass
    class Secret:
        secret: str

    @dataclasses.dataclass
    class TestClass:
        field1: str
        field2: Secret

    obj = TestClass(
        field1='some_thing',
        field2=Secret(
                secret='the secret'
            )
    )

    key = b'6YPPnFEgjAoF-NFmtATGP9wNU0KGnqW2Lm9YP_FLm3s='

    json_cerealizer = JsonCerealizer()
    json_cerealizer.registry[Encrypted] = EncryptedCerealizer({'the_key': key}, json_cerealizer)

    serialized = json_cerealizer.serialize(obj, TestClass)
    assert json_cerealizer.deserialize(serialized, TestClass) == obj

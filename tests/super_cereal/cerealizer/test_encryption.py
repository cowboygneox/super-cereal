import dataclasses

import pytest
from Crypto.Random import get_random_bytes

from super_cereal.cerealizer.encryption import Encrypted
from super_cereal.cerealizer.json import JsonCerealizer


@pytest.mark.parametrize('obj', ['stuff', 42, 12.552, True], ids=[str, int, float, bool])
def test_simple_serialization(obj: any):
    encryption = Encrypted[type(obj)](
        key_id='the_key',
        value=obj
    )

    key = get_random_bytes(16)
    cerealizer = JsonCerealizer({'the_key': key})

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

    key = get_random_bytes(16)
    cerealizer = JsonCerealizer({'the_key': key})

    serialized = cerealizer.serialize(encryption)
    assert cerealizer.deserialize(serialized, Encrypted[TestClass]) == encryption


def test_serializes_encrypted_object():
    @dataclasses.dataclass
    class Secret:
        secret: str

    @dataclasses.dataclass
    class TestClass:
        field1: str
        field2: Encrypted[Secret]

    obj = TestClass(
        field1='some_thing',
        field2=Encrypted(
            key_id='the_key',
            value=Secret(
                secret='the secret'
            )
        )
    )

    key = get_random_bytes(16)
    json_cerealizer = JsonCerealizer({'the_key': key})

    serialized = json_cerealizer.serialize(obj, TestClass)
    assert json_cerealizer.deserialize(serialized, TestClass) == obj


def test_cannot_decrypt_object_due_to_missing_key():
    @dataclasses.dataclass
    class Secret:
        secret: str

    @dataclasses.dataclass
    class TestClass:
        field1: str
        field2: Encrypted[Secret]

    obj = TestClass(
        field1='some_thing',
        field2=Encrypted(
            key_id='the_key',
            value=Secret(
                secret='the secret'
            )
        )
    )

    key = get_random_bytes(16)

    cerealizer = JsonCerealizer({'the_key': key})

    serialized = cerealizer.serialize(obj, TestClass)
    serialized['field2']['key_id'] = 'bogus'
    deserialized = cerealizer.deserialize(serialized, TestClass)
    obj.field2 = Encrypted('bogus', None)
    assert deserialized == obj


def test_cannot_decrypt_object_due_to_bad_key():
    @dataclasses.dataclass
    class Secret:
        secret: str

    @dataclasses.dataclass
    class TestClass:
        field1: str
        field2: Encrypted[Secret]

    obj = TestClass(
        field1='some_thing',
        field2=Encrypted(
            key_id='the_key',
            value=Secret(
                secret='the secret'
            )
        )
    )

    key = get_random_bytes(16)

    cerealizer = JsonCerealizer({'the_key': key})

    serialized = cerealizer.serialize(obj, TestClass)

    cerealizer.registry[Encrypted].encryption_keys = {'the_key': get_random_bytes(16)}
    try:
        cerealizer.deserialize(serialized, TestClass)
        assert False
    except ValueError as e:
        assert str(e) == 'MAC check failed'


def test_encryption_repr():
    assert str(Encrypted('key', 'this is super secret')) == 'Encrypted(***)'
    assert repr(Encrypted('key', 'this is super secret')) == 'Encrypted(key_id=key, value=***)'

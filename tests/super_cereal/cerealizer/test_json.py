import dataclasses
from typing import Optional, List

import pytest

from super_cereal.cerealizer import SerializationException, DeserializationException
from super_cereal.cerealizer.json import JsonCerealizer


@pytest.mark.parametrize('obj', ['stuff', 42, 12.552, True], ids=[str, int, float, bool])
def test_serializer_primatives(obj: any):
    cerealizer = JsonCerealizer()
    serialized = cerealizer.serialize(obj)
    assert serialized == obj
    assert cerealizer.deserialize(serialized, type(obj)) == obj


def test_serializer_simple_object():
    @dataclasses.dataclass
    class TestClass:
        field1: str
        field2: int
        field3: float
        field4: bool
        field6: List[str]
        field7: Optional[str]
        field8: Optional[str]

    cerealizer = JsonCerealizer()
    obj = TestClass('stuff', 42, 12.552, True, ['1', '2', '3'], 'another', None)

    serialized = cerealizer.serialize(obj)
    assert serialized == {
        'field1': 'stuff',
        'field2': 42,
        'field3': 12.552,
        'field4': True,
        'field6': ['1', '2', '3'],
        'field7': 'another',
        'field8': None
    }
    assert obj == cerealizer.deserialize(serialized, TestClass)


def test_serializer_complex_object():
    @dataclasses.dataclass
    class AnotherClass:
        field: int

    @dataclasses.dataclass
    class TestClass:
        field1: str
        field2: Optional[List[AnotherClass]]
        field3: Optional[List[AnotherClass]]

    cerealizer = JsonCerealizer()
    obj = TestClass('stuff', [AnotherClass(42), AnotherClass(27)], None)
    serialized = cerealizer.serialize(obj)
    assert serialized == {
        'field1': 'stuff',
        'field2': [{'field': 42}, {'field': 27}],
        'field3': None
    }
    deserialized = cerealizer.deserialize(serialized, TestClass)
    assert obj == deserialized


def test_wrong_type():
    @dataclasses.dataclass
    class TestClass:
        field1: str
        field2: str

    cerealizer = JsonCerealizer()
    # noinspection PyTypeChecker
    obj = TestClass(42, 'stuff')
    serialized = cerealizer.serialize(obj)
    assert serialized == {'field1': '42', 'field2': 'stuff'}

    deserialize = cerealizer.deserialize(serialized, TestClass)
    assert obj != deserialize

    obj.field1 = '42'
    assert obj == deserialize


def test_no_annotations():
    class TestClass:
        def __init__(self, bogus, argument):
            pass

    cerealizer = JsonCerealizer()

    obj = TestClass('something', 2433)

    try:
        cerealizer.serialize(obj)
        assert False
    except SerializationException as e:
        msg = '"tests.super_cereal.cerealizer.test_json.TestClass": "bogus" has no annotation.'
        assert str(e) == msg
    except Exception:
        assert False

    payload = {'bogus': 'something', 'arugment': 2433}

    try:
        cerealizer.deserialize(payload, TestClass)
        assert False
    except DeserializationException as e:
        msg = '"tests.super_cereal.cerealizer.test_json.TestClass": "bogus" has no annotation.'
        assert str(e) == msg
    except Exception:
        assert False


# TODO these exceptions are garbage. Not sure how to make them better now, but it's at least something...
def test_vague_annotations():
    @dataclasses.dataclass
    class TestClass:
        field1: any

    cerealizer = JsonCerealizer()

    obj = TestClass('something')

    try:
        cerealizer.serialize(obj)
        assert False
    except SerializationException as e:
        msg = '"builtins.any": "args" has no annotation.'
        assert str(e) == msg
    except Exception:
        assert False

    payload = {'field1': 'something'}

    try:
        cerealizer.deserialize(payload, TestClass)
        assert False
    except DeserializationException as e:
        msg = '"builtins.any": "kwargs" has no annotation.'
        assert str(e) == msg
    except Exception:
        assert False

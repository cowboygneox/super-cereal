import dataclasses
from typing import Optional, List

import pytest

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
    deserialized = cerealizer.deserialize(serialized, TestClass)
    assert obj == deserialized


def test_serializer_complex_object():
    @dataclasses.dataclass
    class AnotherClass:
        field: int

    @dataclasses.dataclass
    class TestClass:
        field1: str
        field2: Optional[List[AnotherClass]]

    cerealizer = JsonCerealizer()
    obj = TestClass('stuff', [AnotherClass(42), AnotherClass(27)])
    serialized = cerealizer.serialize(obj)
    deserialized = cerealizer.deserialize(serialized, TestClass)
    assert obj == deserialized

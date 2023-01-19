import dataclasses
from typing import Optional

import pytest

from super_cereal.cerealizer.json import JsonCerealizer


@pytest.mark.parametrize('obj', ['stuff', 42, 12.552, True])
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
        field5: Optional[str]
        field6: Optional[str]

    cerealizer = JsonCerealizer()
    obj = TestClass('stuff', 42, 12.552, True, 'another', None)
    serialized = cerealizer.serialize(obj)
    deserialized = cerealizer.deserialize(serialized, TestClass)
    assert obj == deserialized

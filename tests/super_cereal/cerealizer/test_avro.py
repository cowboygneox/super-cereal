import dataclasses
from typing import Optional, List

import pytest

from super_cereal.cerealizer.avro import AvroCerealizer


@pytest.mark.parametrize('obj', ['stuff', 42, 12.552, True], ids=[str, int, float, bool])
def test_serializer_primatives(obj: any):
    cerealizer = AvroCerealizer()
    serialized = cerealizer.serialize(obj)
    assert cerealizer.deserialize(serialized, type(obj)) == obj


def test_simple_obj():
    @dataclasses.dataclass
    class TestClass:
        field1: str
        field2: int
        field3: float
        field4: bool
        field6: List[str]
        field7: Optional[str]
        field8: Optional[str]

    cerealizer = AvroCerealizer()
    obj = TestClass('stuff', 42, 12.552, True, ['stuff', 'things'], 'str', None)

    serialized = cerealizer.serialize(obj)
    deserialized = cerealizer.deserialize(serialized, TestClass)
    assert obj == deserialized


def test_complex_obj():
    @dataclasses.dataclass
    class AnotherClass:
        field: int

    @dataclasses.dataclass
    class AnotherClass2:
        field: int

    @dataclasses.dataclass
    class AnotherClass3:
        field: int

    @dataclasses.dataclass
    class TestClass:
        field1: str
        field2: AnotherClass
        field3: List[AnotherClass2]
        field4: Optional[List[AnotherClass3]]

    cerealizer = AvroCerealizer()
    obj = TestClass('stuff', AnotherClass(1), [AnotherClass2(2), AnotherClass2(3)], None)

    serialized = cerealizer.serialize(obj)
    deserialized = cerealizer.deserialize(serialized, TestClass)
    assert obj == deserialized
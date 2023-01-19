import pytest

from super_cereal.cerealizer.json import JsonCerealizer


@pytest.mark.parametrize('obj', ['stuff', 42, 12.552, True])
def test_serializer(obj: any):
    cerealizer = JsonCerealizer()
    assert cerealizer.deserialize(cerealizer.serialize(obj), str) == obj

import inspect
import typing
from typing import List, Tuple

from super_cereal.cerealizer import Cerealizer, T


class JsonCerealizer(Cerealizer[T, typing.Union[str, float, int, bool, type(None), dict]]):
    def serialize(self, obj: T) -> typing.Union[str, float, int, bool, type(None), dict]:
        if type(obj) in [str, float, int, bool, type(None)]:
            return obj

        # noinspection PyTypeChecker
        fields: List[Tuple[str, inspect.Parameter]] = list(inspect.signature(type(obj).__init__).parameters.items())[1:]

        return {field: self.serialize(getattr(obj, field)) for field, param in fields}

    def deserialize(self, obj: typing.Union[str, float, int, bool, type(None), dict], t: T) -> T:
        if type(obj) in [str, float, int, bool, type(None)]:
            return obj

        if typing.get_origin(t) == typing.Union:
            t1, t2 = typing.get_args(t)
            return self.deserialize(obj, t1)

        # noinspection PyTypeChecker
        fields: List[Tuple[str, inspect.Parameter]] = list(inspect.signature(t.__init__).parameters.items())[1:]

        fixed = {
            field: self.deserialize(obj[field], param.annotation)
            for field, param in fields
        }

        return t(**fixed)

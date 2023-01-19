import inspect
import typing
from typing import List, Tuple

from super_cereal.cerealizer import Cerealizer, T

JsonTypes = typing.Union[str, float, int, bool, type(None), list, dict]


class JsonCerealizer(Cerealizer[T, JsonTypes]):
    def serialize(self, obj: T) -> JsonTypes:
        if type(obj) in [str, float, int, bool, type(None)]:
            return obj
        if type(obj) in [list]:
            return [self.serialize(v) for v in obj]

        # noinspection PyTypeChecker
        fields: List[Tuple[str, inspect.Parameter]] = list(inspect.signature(type(obj).__init__).parameters.items())[1:]

        return {field: self.serialize(getattr(obj, field)) for field, param in fields}

    def deserialize(self, obj: JsonTypes, t: T) -> T:
        if t in [str, float, int, bool, type(None)]:
            return obj
        if typing.get_origin(t) in [list]:
            return [self.deserialize(v, typing.get_args(t)[0]) for v in obj]

        if typing.get_origin(t) == typing.Union:
            args = typing.get_args(t)
            if len(args) == 2 and args[1] is type(None):
                return self.deserialize(obj, args[0])

        # noinspection PyTypeChecker
        fields: List[Tuple[str, inspect.Parameter]] = list(inspect.signature(t.__init__).parameters.items())[1:]

        fixed = {
            field: self.deserialize(obj[field], param.annotation)
            for field, param in fields
        }

        return t(**fixed)

import inspect
import typing
from typing import List, Tuple

from super_cereal.cerealizer import Cerealizer, T, SerializationException, DeserializationException

JsonTypes = typing.Union[str, float, int, bool, type(None), list, dict]


class JsonCerealizer(Cerealizer[T, JsonTypes]):
    def serialize(self, obj: T) -> JsonTypes:
        def _serialize(obj: T, expected_type: type):
            if expected_type in [type(None)]:
                return None
            if expected_type in [str, float, int, bool]:
                return expected_type(obj)
            if typing.get_origin(expected_type) in [list]:
                t = typing.get_args(expected_type)[0]
                return [_serialize(v, t) for v in obj]
            if typing.get_origin(expected_type) in [typing.Union]:
                for t in typing.get_args(expected_type):
                    if type(obj) == t:
                        return _serialize(obj, t)
                    if type(obj) == typing.get_origin(t):
                        return _serialize(obj, t)

            # noinspection PyTypeChecker
            fields: List[Tuple[str, inspect.Parameter]] = list(
                inspect.signature(type(obj).__init__).parameters.items())[1:]

            for field, param in fields:
                # noinspection PyUnresolvedReferences,PyProtectedMember
                if param.annotation == inspect._empty:
                    class_name = f'"{expected_type.__module__}.{expected_type.__name__}"'
                    raise SerializationException(f'{class_name}: "{field}" has no annotation.')

            return {field: _serialize(getattr(obj, field), param.annotation) for field, param in fields}

        return _serialize(obj, type(obj))

    def deserialize(self, obj: JsonTypes, t: T) -> T:
        if t in [type(None)]:
            return None
        if t in [str, float, int, bool]:
            return t(obj)
        if typing.get_origin(t) in [list]:
            return [self.deserialize(v, typing.get_args(t)[0]) for v in obj]

        if typing.get_origin(t) == typing.Union:
            args = typing.get_args(t)
            for arg in args:
                if arg == type(obj):
                    return self.deserialize(obj, arg)
                if typing.get_origin(arg) == type(obj):
                    return self.deserialize(obj, arg)

        # noinspection PyTypeChecker
        fields: List[Tuple[str, inspect.Parameter]] = list(inspect.signature(t.__init__).parameters.items())[1:]

        for field, param in fields:
            # noinspection PyUnresolvedReferences,PyProtectedMember
            if param.annotation == inspect._empty:
                class_name = f'"{t.__module__}.{t.__name__}"'
                raise DeserializationException(f'{class_name}: "{field}" has no annotation.')

        fixed = {
            field: self.deserialize(obj[field], param.annotation)
            for field, param in fields
        }

        return t(**fixed)

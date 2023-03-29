import inspect
import typing

from super_cereal.cerealizer import Cerealizer, T, V, SerializationException, DeserializationException


class PassthruCerealizer(Cerealizer[any, any]):
    def serialize(self, obj: any, t: any = None) -> any:
        return None if obj is None else t(obj)

    def deserialize(self, obj: any, t: any) -> any:
        return None if obj is None else t(obj)


class EnumCerealizer(Cerealizer):
    def serialize(self, obj: any, t: T = None) -> V:
        return obj.name

    def deserialize(self, obj: V, t: T) -> T:
        return t[obj]


class ListCerealizer(Cerealizer):
    def serialize(self, obj: any, t: T = None) -> V:
        t = typing.get_args(t)[0]
        return [self.registry[t].serialize(v, t) for v in obj]

    def deserialize(self, obj: V, t: T) -> T:
        t = typing.get_args(t)[0]
        return [self.registry[t].deserialize(v, t) for v in obj]


class UnionCerealizer(Cerealizer):
    def serialize(self, obj: any, t: T = None) -> V:
        for t1 in typing.get_args(t):
            if type(obj) == t1:
                return self.registry[t1].serialize(obj, t1)
            if type(obj) == typing.get_origin(t1):
                return self.registry[t1].serialize(obj, t1)

        raise NotImplementedError()

    def deserialize(self, obj: V, t: T) -> T:
        args = typing.get_args(t)
        for arg in args:
            if arg == type(obj):
                return self.registry[arg].deserialize(obj, arg)
            if typing.get_origin(arg) == type(obj):
                return self.registry[arg].deserialize(obj, arg)

        raise NotImplementedError()


class DictCerealizer(Cerealizer):
    def serialize(self, obj: any, t: T = None) -> V:
        if t == dict or typing.get_origin(t) == dict:
            return obj

        # noinspection PyTypeChecker
        fields: typing.List[typing.Tuple[str, inspect.Parameter]] = list(
            inspect.signature(t.__init__).parameters.items())[1:]

        for field, param in fields:
            # noinspection PyUnresolvedReferences,PyProtectedMember
            if param.annotation == inspect._empty:
                class_name = f'"{t.__module__}.{t.__name__}"'
                raise SerializationException(f'{class_name}: "{field}" has no annotation.')

        fixed_fields = {}

        for field, param in fields:
            cerealizer = self.registry[param.annotation]
            fixed_fields[field] = cerealizer.serialize(getattr(obj, field), param.annotation)

        return fixed_fields

    def deserialize(self, obj: V, t: T) -> T:
        if t == dict or typing.get_origin(t) == dict:
            return obj

        # noinspection PyTypeChecker
        fields: typing.List[
            typing.Tuple[str, inspect.Parameter]] = list(inspect.signature(t.__init__).parameters.items())[1:]

        for field, param in fields:
            # noinspection PyUnresolvedReferences,PyProtectedMember
            if param.annotation == inspect._empty:
                class_name = f'"{t.__module__}.{t.__name__}"'
                raise DeserializationException(f'{class_name}: "{field}" has no annotation.')

        fixed = {
            field: self.registry[param.annotation].deserialize(obj[field], param.annotation)
            for field, param in fields
        }

        return t(**fixed)

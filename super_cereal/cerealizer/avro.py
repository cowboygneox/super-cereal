import inspect
import io
import json
from enum import EnumMeta
from typing import Union, get_origin, get_args, Dict, List, Tuple

from avro.datafile import DataFileReader
from avro.io import DatumReader

from super_cereal.cerealizer import Cerealizer, V, T
from super_cereal.cerealizer.encryption import Encrypted
from super_cereal.cerealizer.json import JsonCerealizer

BUILTIN_ALIASES = {
    str: 'string',
    int: 'int',
    bytes: 'bytes',
    float: 'double',
    bool: 'boolean',
    type(None): 'null',
}


class AvroCerealizer(Cerealizer):
    def __init__(self, encryption_keys: Dict[str, bytes] = None) -> None:
        super().__init__(encryption_keys)
        self.json_serializer = JsonCerealizer(encryption_keys)

    @staticmethod
    def get_schema(record: type) -> Dict[str, any]:
        def get_schema(t: type, namespace: str) -> Union[Dict[str, any], List[Dict[str, any]]]:
            if t in BUILTIN_ALIASES:
                return {'type': BUILTIN_ALIASES[t]}
            if t == list or get_origin(t) == list:
                arg = get_args(t)[0]
                if arg in BUILTIN_ALIASES:
                    return {'type': 'array', 'items': BUILTIN_ALIASES[arg]}
                return {'type': 'array', 'items': get_schema(arg, namespace)}
            if type(t) == EnumMeta:
                # noinspection PyProtectedMember,PyUnresolvedReferences
                return {
                    "type": "enum",
                    "name": t.__name__,
                    "symbols": t._member_names_
                }
            if Union == get_origin(t):
                args = get_args(t)

                def type_for_arg(a):
                    return BUILTIN_ALIASES[a] if a in BUILTIN_ALIASES else get_schema(a, namespace)

                return [{'type': type_for_arg(z)} for z in args]
            if Encrypted == get_origin(t):
                schemas = get_schema(get_args(t)[0], f'{namespace}.{get_origin(t).__name__}.value')

                if not isinstance(schemas, list):
                    schemas = [schemas]

                str_schema = get_schema(str, namespace)
                if str_schema not in schemas:
                    schemas.append(str_schema)

                return {
                    'namespace': namespace,
                    'type': 'record',
                    'name': get_origin(t).__name__,
                    'fields': [
                        {'name': 'key_id', 'type': 'string'},
                        {'name': 'value', 'type': schemas},
                        {'name': 'tag', 'type': 'string'},
                        {'name': 'nonce', 'type': 'string'},
                    ]
                }

            # noinspection PyTypeChecker
            fields: List[Tuple[str, inspect.Parameter]] = list(inspect.signature(t.__init__).parameters.items())[1:]

            f = []

            for field in fields:
                def should_simplify(tp):
                    return tp in BUILTIN_ALIASES or Union == get_origin(tp)

                schema = get_schema(field[1].annotation, namespace=f'{namespace}.{t.__name__}.{field[0]}')
                f.append({
                    'name': field[0],
                    'type': schema['type'] if should_simplify(field[1].annotation) else schema
                })

            return {
                'namespace': f'{inspect.getmodule(t).__name__}{namespace}',
                'type': 'record',
                'name': t.__name__,
                'fields': f
            }

        return get_schema(record, inspect.getmodule(record).__name__)

    def serialize(self, obj: any, t: T = None) -> V:
        import avro.schema
        from avro.datafile import DataFileWriter
        from avro.io import DatumWriter

        the_json = self.get_schema(type(obj))
        schema_json = json.dumps(the_json)
        schema = avro.schema.parse(schema_json)

        with io.BytesIO() as bytes_io:
            with DataFileWriter(bytes_io, DatumWriter(), schema) as writer:
                writer.append(self.json_serializer.serialize(obj))
                writer.flush()
                return bytes_io.getvalue()

    def deserialize(self, obj: bytes, t: T) -> T:
        with io.BytesIO(obj) as bytes_io:
            with DataFileReader(bytes_io, DatumReader()) as reader:
                for msg in reader:
                    return self.json_serializer.deserialize(msg, t)

        return None

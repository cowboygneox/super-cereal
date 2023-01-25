import inspect
import io
import json
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
    def __init__(self) -> None:
        super().__init__()
        self.json_serializer = JsonCerealizer()

    @staticmethod
    def get_schema(record: type) -> Dict[str, any]:
        if record in BUILTIN_ALIASES:
            return {'type': BUILTIN_ALIASES[record]}

        def get_field_name(t):
            if t in BUILTIN_ALIASES:
                return BUILTIN_ALIASES[t]
            if t == list or get_origin(t) == list:
                return {'type': 'array', 'items': get_field_name(get_args(t)[0])}
            if Union == get_origin(t):
                args = get_args(t)
                return [get_field_name(z) for z in args]
            if Encrypted == get_origin(t):
                return {
                    'namespace': 'avant.messaging.serialization',
                    'type': 'record',
                    'name': 'Encrypted',
                    'fields': [
                        {'name': 'key_id', 'type': 'string'},
                        {'name': 'value', 'type': get_field_name(get_args(t)[0])},
                    ]
                }

            # This is definitely not kosher. There needs to be a mechanism to verify this is a Record.
            return AvroCerealizer.get_schema(t)

        # noinspection PyTypeChecker
        fields: List[Tuple[str, inspect.Parameter]] = list(inspect.signature(record.__init__).parameters.items())[1:]

        f = []

        for field in fields:
            f.append({
                'name': field[0],
                'type': get_field_name(field[1].annotation)
            })

        return {
            'namespace': inspect.getmodule(record).__name__,
            'type': 'record',
            'name': record.__name__,
            'fields': f
        }

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

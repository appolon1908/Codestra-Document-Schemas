"""Offline access to Codestra's standalone JSON Schema contracts."""
import json
from importlib.resources import files

__version__ = '1.0.0'
SCHEMA_NAMES = ('extraction-envelope', 'do-driver-licence', 'reviewed-result',
                'client-intake', 'error', 'worker-contract')


def load_schema(name: str) -> dict:
    """Return a fresh v1 schema. No filesystem paths or remote refs are accepted."""
    if name not in SCHEMA_NAMES:
        raise ValueError(f'Unknown schema: {name}')
    resource = files(__package__).joinpath('schemas', 'v1', name + '.schema.json')
    return json.loads(resource.read_text(encoding='utf-8'))


def validate(name: str, instance: object) -> None:
    """Validate without coercion; raises jsonschema.ValidationError on invalid input.

    Requires the package's `validation` extra. Errors may contain input PII;
    callers must not log exception representations or raw validator output.
    """
    from jsonschema import Draft202012Validator, FormatChecker
    from rfc3339_validator import validate_rfc3339  # noqa: F401; fail closed if unavailable
    Draft202012Validator(load_schema(name), format_checker=FormatChecker()).validate(instance)

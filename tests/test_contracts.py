import json
from pathlib import Path
import unittest
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SCHEMAS = ROOT / 'codestra_document_schemas/schemas/v1'
NAMES = {'extraction-envelope', 'do-driver-licence', 'reviewed-result',
         'client-intake', 'error', 'worker-contract'}

class Contracts(unittest.TestCase):
    def test_catalog_complete(self):
        self.assertEqual({p.name.removesuffix('.schema.json') for p in SCHEMAS.glob('*.json')}, NAMES)

    def test_fixtures(self):
        manifest_path = ROOT / 'examples/manifest.json'
        self.assertTrue(manifest_path.exists(), 'Shared fixture manifest is required')
        manifest = json.loads(manifest_path.read_text())
        self.assertGreaterEqual(len(manifest), 40)
        covered = set()
        for case in manifest:
            with self.subTest(case=case['path']):
                schema = json.loads((SCHEMAS / (case['schema'] + '.schema.json')).read_text())
                Draft202012Validator.check_schema(schema)
                validator = Draft202012Validator(schema, format_checker=FormatChecker())
                instance = json.loads((ROOT / 'examples' / case['path']).read_text())
                self.assertEqual(validator.is_valid(instance), case['valid'])
                covered.add((case['schema'], case['valid']))
        self.assertEqual(covered, {(name, valid) for name in NAMES for valid in [True, False]})


class Package(unittest.TestCase):
    def test_loader(self):
        from codestra_document_schemas import load_schema, validate, __version__
        with self.assertRaises(ValueError):
            load_schema('../error')
        first = load_schema('error')
        first['title'] = 'mutated'
        self.assertNotEqual(load_schema('error')['title'], 'mutated')
        self.assertEqual(__version__, json.loads((ROOT / 'package.json').read_text())['version'])
        validate('error', json.loads((ROOT / 'examples/valid/error.json').read_text()))
        from jsonschema import ValidationError
        with self.assertRaises(ValidationError):
            validate('reviewed-result', json.loads((ROOT / 'examples/invalid/reviewed-invalid-timestamp.json').read_text()))

    def test_standalone_and_generation(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location('builder', ROOT / 'scripts/build_schemas.py')
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        before = {p.name: p.read_bytes() for p in SCHEMAS.glob('*.json')}
        builder.build()
        self.assertEqual(before, {p.name: p.read_bytes() for p in SCHEMAS.glob('*.json')})
        def check(node):
            if isinstance(node, dict):
                if '$ref' in node:
                    self.assertTrue(node['$ref'].startswith('#/$defs/'))
                for value in node.values():
                    check(value)
            elif isinstance(node, list):
                for value in node:
                    check(value)
        for data in before.values():
            check(json.loads(data))

if __name__ == '__main__':
    unittest.main()

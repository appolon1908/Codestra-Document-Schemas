# Codestra Document Schemas

Version **1.0.0** provides standalone, reusable JSON Schema **2020-12** contracts for document extraction, review and downstream intake. No services, environment variables or runtime secrets are needed. Every schema has only local `$ref` references and can validate offline.

| Schema | Purpose | Retention boundary |
| --- | --- | --- |
| `extraction-envelope` | Generic normalized extraction and evidence | Transient; contains OCR/QR content |
| `do-driver-licence` | Dominican Republic driver licence extraction | Transient; includes clear document number |
| `reviewed-result` | Confirmed DR licence result | Persistence allowlist; hash and last four only |
| `client-intake` | Minimal reviewed identity for consumers such as FACE-ID | No images, OCR evidence, QR or biometric payload |
| `error` | Bounded error codes and retry hint | No freeform messages or exception payloads |
| `worker-contract` | DR extraction request, success or failure message | Successful result is transient |

Canonical JSON files are in [`codestra_document_schemas/schemas/v1`](codestra_document_schemas/schemas/v1). `$id` URLs identify contracts; they do not require a live schema hosting service. `schema_version` is exactly `1.0.0`. Python and JavaScript packages ship the same files. These contracts do not authenticate a document or authorize an operation.

## Python

From a checkout:

```sh
python -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m unittest discover -s tests -v
```

```python
from codestra_document_schemas import load_schema, validate

schema = load_schema('do-driver-licence')
validate('do-driver-licence', extraction)  # raises jsonschema.ValidationError
```

Install the `validation` extra when using `validate`; loading schema dictionaries needs only the standard library. Do not log validation exception text: it can contain the invalid input.

## JavaScript

```sh
npm ci
npm test
```

```javascript
const Ajv2020 = require('ajv/dist/2020');
const addFormats = require('ajv-formats');
const { loadSchema } = require('@codestra/document-schemas');
const ajv = new Ajv2020({ strict: true, allErrors: true });
addFormats(ajv);
const validate = ajv.compile(loadSchema('client-intake'));
const accepted = validate(projection);
```

Consumer applications install `ajv` and `ajv-formats` themselves. Enable calendar format checks; do not use coercion, automatic defaults or removal of additional properties. Draft 2020-12 treats format assertion as optional, so a validator without format checks is insufficient for these contracts. See the [JSON Schema validation specification](https://json-schema.org/draft/2020-12/json-schema-validation#section-7).

## Examples and verification

[`examples/manifest.json`](examples/manifest.json) maps every synthetic fixture to its schema and expected acceptance. The fixtures include impossible dates, missing fields, nested unknown properties, malformed digests, worker branch violations and persistence leaks. All names, identifiers, QR text and digests are fabricated. Repeated hex digests are shape examples, not computed values. Never replace these fixtures with production data.

Both language suites consume the same manifest. `scripts/build_schemas.py` regenerates schemas deterministically; `scripts/build_fixtures.py` regenerates examples. Checked-in JSON files are the distribution artifacts; consumers do not run generators.

See [architecture and field semantics](docs/architecture.md), [versioning, migration and release policy](docs/versioning.md), and [changelog](CHANGELOG.md). No license grant is added by this foundation; package metadata marks the project proprietary/unlicensed pending an owner decision.

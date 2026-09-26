# Versioning, migration and release policy

Package versions use semantic versioning. v1 payloads declare `schema_version: "1.0.0"`; the schemas live under `schemas/v1/` with stable IDs under `https://schemas.codestra.dev/document-intelligence/v1/`. These IDs identify resources even when the hosting domain is unavailable. There is no implicit `latest` schema and no network resolver requirement.

Once released, v1 acceptance behavior is frozen. A change to accepted payloads—including a required field, enum, field removal, new field on a closed object, changed nullability, unit, pattern, hash recipe or privacy rule—requires a new major schema directory and IDs. Documentation, tests and compatible packaging fixes may ship as package patches without changing the payload version. A package can include multiple major schema directories; adding another independent profile can be a package minor only when existing contracts remain byte-for-byte unchanged. Consumers pin a package release and select an exact contract.

## Migration

1. Read the payload's explicit version and document profile. Reject unknown versions or route to a deliberate adapter; never guess a version from fields.
2. Validate with the source version, apply a reviewed deterministic adapter, then validate with the destination version. Maintain golden synthetic before/after fixtures and cross-language tests.
3. Deploy readers capable of both versions before enabling new writers. Measure version-specific rejection counts without logging payloads. Keep old readers until old records and queued messages have expired or migrated.
4. Persist the destination version with the migrated record. Keep a rollback path to the old reader and writer; do not silently reinterpret old units, dates, identifiers or hashes.

The first release has no legacy migration adapter. Importing legacy records containing clear numbers requires a transient, controlled transformation that derives the hash and last four, allowlists reviewed fields, validates the destination and removes clear numbers and evidence from persistent destinations. It must not copy the legacy object wholesale. A record without sufficient identity/review information cannot be promoted automatically.

Key rotation changes `document_hash_key_id` and hash values. Rehashing requires authorized transient access to the original number; last four digits cannot reconstruct it. Applications must define reconciliation and rotation separately. Never introduce clear-number persistence to make migration convenient.

## Release verification

```sh
python scripts/build_schemas.py
python scripts/build_fixtures.py
.venv/bin/python -m unittest discover -s tests -v
npm ci
npm test
.venv/bin/python -m build
npm pack --dry-run
```

Inspect wheel, source distribution and npm archive contents to ensure all six schemas ship and no caches, secrets or environment-specific files are included. Check that Python, npm and changelog versions agree. Install the wheel and load schemas from package resources outside the source import path; smoke-test the npm tarball similarly. `scripts/validate.sh` provides a portable CI entry point for both validator suites, regeneration checks and distribution builds; publishing remains a separate owner-managed release action.

Use a reviewed immutable Git tag such as `v1.0.0` for an actual release. Registry credentials belong only in the release environment and are not required for tests or runtime schema loading. A branch push is not a package publication, release tag or merge.

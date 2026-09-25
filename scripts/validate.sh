#!/usr/bin/env sh
# Run from the repository root after installing Python dev extras and npm dependencies.
set -eu
python -m unittest discover -s tests -v
npm test
python scripts/build_schemas.py
python scripts/build_fixtures.py
git diff --exit-code -- codestra_document_schemas/schemas examples
python -m build
npm pack --dry-run

#!/usr/bin/env sh
set -eu

if [ -n "${PYTHON:-}" ]; then
  PY="$PYTHON"
elif [ -x .venv/bin/python ]; then
  PY=.venv/bin/python
else
  PY=python3
fi

"$PY" -m unittest discover -s tests -v
npm test
"$PY" scripts/build_schemas.py
"$PY" scripts/build_fixtures.py
git diff --exit-code -- codestra_document_schemas/schemas examples
"$PY" -m build
npm pack --dry-run

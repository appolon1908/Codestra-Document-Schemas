# Missions 06-10 — Schema Department
06 Base envelope: schema_id, schema_version, document_type, fields, provenance and validation.
07 Registry: deterministic schema lookup by type/version; unknown versions fail closed.
08 Initial types: identity_card, passport, invoice, contract, bank_statement and generic_document.
09 Validation logic: required fields/type constraints and document-specific validators are separated from OCR engine logic.
10 Compatibility: additive evolution rules and fixtures support API/SDK contract tests.

Implementation branch target after architecture baseline is committed: feature/schema-foundation-v1.

# Architecture and contract semantics

## Data flow and trust boundaries

A worker receives an `extract.request` referencing tenant-scoped opaque asset IDs. The caller resolves those IDs to image/PDF bytes through its own authorized storage. URLs, tokens and inline image data are excluded from the worker input. The worker emits exactly one terminal success or failure per attempt; queue delivery can repeat, so consumers deduplicate by `(tenant_id, job_id, attempt, kind)` and reject conflicting terminal responses.

A success contains a transient `do-driver-licence` extraction, which also conforms to the generic envelope. Review produces a *new* `reviewed-result` object from an explicit allowlist. Intake projects that reviewed object into another explicit allowlist. Never persist or forward an extraction by spreading it into a reviewed object or deleting just `document_number`: raw evidence and QR data can repeat the number.

The worker schema validates message shape. Applications must enforce matching nested/outer `scan_id`, `tenant_id` and `schema_version`, asset ownership, unique input sides, deadlines, attempt progression, response correlation and idempotency. No queue, OCR vendor, database or transport is prescribed. v1 worker messages deliberately support only the DR licence profile. The generic envelope is available independently for other document profiles.

## Extraction envelope

All envelope keys are required: `scan_id`, `tenant_id`, `document_type`, `country`, `schema_version`, `engine`, `fields`, `field_evidence`, `warnings`, `qr_evidence`, `content_digests`. IDs are bounded ASCII tokens, not credentials. `country` uses an uppercase two-letter shape; generic validation does not establish ISO membership. `DO` and `driver_licence` are fixed by the DR profile.

Generic fields are bounded string/number/boolean/null values keyed by snake_case names. Nested arbitrary payloads are not permitted. The DR profile closes this map to the 15 fields below. Every DR field key is required; `null` means unavailable/unreadable. Empty and whitespace-only strings are invalid. An unreadable field is null with a `MISSING_FIELD` warning, not a guessed value. Warnings and evidence may be empty; the application enforces completeness and its confidence policy.

| DR field | Normalized representation |
| --- | --- |
| `full_name` | Nonblank string, at most 200 characters |
| `document_number` | 11 ASCII digits, optionally `000-0000000-0` grouping; transient only |
| `address` | Nonblank string, at most 500 characters |
| `height` | Number in metres, 0.3–3 |
| `weight_lb` | Number in pounds, 1–1500 |
| `sex` | `M`, `F`, or `X`; unreadable/unmapped values become null |
| `blood_type` | `A+`, `A-`, `B+`, `B-`, `AB+`, `AB-`, `O+`, `O-` |
| `birth_date`, `issue_date`, `expiry_date`, `first_issue_date` | Calendar-valid `YYYY-MM-DD` |
| `category` | Uppercase alphanumeric token with spaces, periods, slashes or hyphens; at most 20 characters |
| `restriction` | Nonblank string, at most 200 characters; preserve normalized text |
| `card_serial` | Alphanumeric/hyphen token, at most 40 characters |

These are v1 integration conventions, not a claim of exhaustive issuer formats, legal sex markers, valid categories or official number-checksum rules. Producers map units and dates before validation. Preserve uncertain OCR only in transient evidence and send the record to review; do not coerce it into an apparently valid field.

Field evidence records source (`ocr`, `qr`, `derived`), confidence in `[0,1]`, optional one-based page, normalized bounding box and transient raw text. Bounding boxes are `[x_min, y_min, x_max, y_max]`; applications check coordinate ordering and association with the correct page. Confidence is an engine score, not proof of authenticity. Evidence keys must name a DR field in that profile; generic consumers check that evidence keys correspond to extracted fields.

QR evidence status is `not_detected`, `unreadable` or `decoded`. Only decoded QR evidence permits a raw payload or payload digest, and the digest is required when decoded. Hash raw QR UTF-8 bytes without reserialization. Content digests are `sha256:` followed by 64 lowercase hex characters over the exact original input bytes, with a role of `front`, `back` or `document`. Digests do not prove trustworthiness or bind a document to a person. Raw extraction and evidence require transient handling, bounded retention and exclusion from routine logs.

## Reviewed result and persistence

A reviewed result has `status: confirmed`, review method (`human` or `policy`), reviewer/policy ID, UTC review timestamp and all non-number DR fields. `full_name` must be nonnull; other field values can remain null. Applications decide whether remaining unknowns prevent confirmation. Pending/rejected reviews are not confirmed results and must not use this schema.

`document_number` is absent from the reviewed field allowlist and is explicitly rejected by closed objects. `document_hash`, `document_last4` and `document_hash_key_id` are required. Raw OCR evidence, QR payloads, images, biometrics and freeform review notes are excluded. `card_serial` is a distinct printed card identifier, never an alias for the document number. Do not populate it with the document number.

Before discarding the transient number, normalize by removing only the supported hyphens and verifying exactly 11 ASCII digits. Set `document_last4` to the final four digits, preserving leading zeroes. Compute `document_hash` as `hmac-sha256:` plus lowercase hex HMAC-SHA-256 of UTF-8 bytes of the compact JSON array `["DO","driver_licence","<normalized-number>"]` using a tenant-specific secret managed by the application. Use compact JSON without whitespace. `document_hash_key_id` identifies the tenant's key version; it is not a secret. A plain SHA-256 of a low-entropy document number is not this identifier scheme. No secret or hashing runtime is shipped here. If the clear number is unavailable, the application cannot produce a new confirmed record under v1.

Schema validation verifies digest *shape*, not cryptographic correctness, number/last4 correspondence, identity or approval. Closed objects block accidental structural leakage; no schema can prevent PII deliberately written into an allowed name/address/token string. Persistence applications must perform the allowlist mapping, avoid PII in correlation IDs, redact logs and validate before storage. Schema acceptance alone is not a privacy guarantee.

## Client intake and errors

Client intake requires correlation IDs, schema version, fixed country/type, hash/key ID/last4, full name and UTC review timestamp. Address and birth date are optional (null is allowed when included). It omits licence health/physical attributes, card serial, all OCR/QR evidence, raw images and biometric payloads. FACE-ID or another consumer can separately initiate its own workflow; this projection neither contains biometric results nor establishes consent.

Errors contain code, stage, retryable flag and UTC timestamp plus correlation IDs/version. They have no freeform message, stack, request body or arbitrary details map. Consumers own safe localized messages and retry/backoff policy. Worker success is transient even though the error shape contains no raw payload.

All fixed objects use `additionalProperties: false`. Generic fields/evidence are the documented map exceptions. Validation asserts constraints without silently stripping unknown keys. All `$ref`s are local. The [Draft 2020-12 core specification](https://json-schema.org/draft/2020-12/json-schema-core) defines the schema dialect and reference behavior.

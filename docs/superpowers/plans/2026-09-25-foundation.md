# Document schema foundation implementation plan

Goal: publish application-independent JSON Schema 2020-12 v1 contracts, with an explicit transient-to-persistent privacy boundary.

Architecture: six self-contained schemas with local definitions, distributed unchanged in Python and JavaScript packages. Generic extraction is extensible only through bounded scalar fields. DR extraction fixes the field allowlist. Reviewed and intake records use separate allowlists and never inherit transient payload fields. Worker request/success/failure branches are discriminated and closed.

User scope authorizes implementation, testing, commit and push on the existing mission branch, with no merge. Work stays in this worktree. No runtime secrets or services.

1. Write a shared positive/negative fixture harness and contract assertions. Run before schema creation to establish the missing-contract failure.
2. Implement schema files, synthetic fixtures, offline Python/JS validators, and package metadata. Exercise dates, patterns, bounds, nested unknown keys, privacy boundaries and worker branches in both validators.
3. Document architecture, normalized field semantics, consumer responsibilities, versioning, migrations, and release commands. Verify package contents and installed resources.
4. Review all changes, run complete suites, commit and push the named branch. No release publication or merge.

Review focus: missing versus null OCR fields; calendar-invalid dates; persistence leaks via nested evidence/QR/unknown properties; worker result exclusivity; offline distribution parity. JSON Schema cannot verify identities, compute hashes, authorize tenants, compare cross-field dates, or recognize PII deliberately placed in a permitted string.
